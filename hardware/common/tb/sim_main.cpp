#include "Vtb_soc.h"
#include "verilated.h"
#include "verilated_vcd_c.h"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr unsigned kWords = 1024;
constexpr unsigned kBitCycles = 16;
constexpr uint64_t kHalfPeriodNs = 500;

struct Options {
    std::string image, trace, retireLog;
    uint64_t maxCycles = 10000;
    unsigned buttons = 0xa, switches = 0x5;
    std::vector<unsigned> rxBytes;
};

uint64_t number(const std::string& value, uint64_t maximum) {
    if (value.empty() || value.front() == '-') throw std::runtime_error("invalid number: " + value);
    size_t used = 0;
    const auto result = std::stoull(value, &used, 0);
    if (used != value.size() || result > maximum) throw std::runtime_error("number out of range: " + value);
    return result;
}

Options parseOptions(int argc, char** argv) {
    Options options;
    for (int index = 1; index < argc; ++index) {
        const std::string argument = argv[index];
        if (index + 1 == argc) throw std::runtime_error("missing value for " + argument);
        const std::string value = argv[++index];
        if (argument == "--image") options.image = value;
        else if (argument == "--trace") options.trace = value;
        else if (argument == "--retire-log") options.retireLog = value;
        else if (argument == "--max-cycles") options.maxCycles = number(value, UINT64_MAX / 1000);
        else if (argument == "--buttons") options.buttons = number(value, 15);
        else if (argument == "--switches") options.switches = number(value, 15);
        else if (argument == "--rx-byte") options.rxBytes.push_back(number(value, 255));
        else throw std::runtime_error("unknown option: " + argument);
    }
    if (options.image.empty()) throw std::runtime_error("--image FILE is required");
    if (options.maxCycles == 0) throw std::runtime_error("--max-cycles must be positive");
    return options;
}

std::vector<uint16_t> readImage(const std::string& filename) {
    std::ifstream input(filename);
    if (!input) throw std::runtime_error("cannot open image: " + filename);
    std::vector<uint16_t> image;
    std::string line;
    unsigned lineNumber = 0;
    while (std::getline(input, line)) {
        ++lineNumber;
        const auto first = line.find_first_not_of(" \t\r");
        if (first == std::string::npos) continue;
        line = line.substr(first, line.find_last_not_of(" \t\r") - first + 1);
        if (line.size() != 16 || line.find_first_not_of("01") != std::string::npos)
            throw std::runtime_error("image line " + std::to_string(lineNumber) + ": expected one 16-bit binary word");
        image.push_back(static_cast<uint16_t>(std::stoul(line, nullptr, 2)));
        if (image.size() > kWords) throw std::runtime_error("image exceeds 1024 words");
    }
    if (input.bad()) throw std::runtime_error("failed to read image: " + filename);
    if (image.empty()) throw std::runtime_error("image is empty");
    return image;
}

template <typename Packed>
void writeWords(std::ostream& output, const Packed& packed, unsigned count) {
    output << '[';
    for (unsigned index = 0; index < count; ++index) {
        if (index) output << ',';
        output << ((packed[index / 2] >> ((index % 2) * 16)) & 0xffffu);
    }
    output << ']';
}

// Independent pin-level decoder: sample start/data/stop bit centers. The
// expected TX bytes in Python therefore do not rely on a second RTL UART.
class TxMonitor {
    enum State { Idle, Start, Data, Stop } state = Idle;
    uint64_t sampleAt = 0;
    unsigned value = 0, bit = 0;
public:
    std::vector<unsigned> bytes;
    bool idle() const { return state == Idle; }
    void sample(bool pin, uint64_t now) {
        if (state == Idle) {
            if (!pin) {
                state = Start;
                sampleAt = now + kBitCycles / 2;
            }
            return;
        }
        if (now != sampleAt) return;
        sampleAt += kBitCycles;
        if (state == Start) {
            if (pin) throw std::runtime_error("UART TX start bit is too short");
            value = bit = 0;
            state = Data;
        } else if (state == Data) {
            value |= unsigned(pin) << bit;
            if (++bit == 8) state = Stop;
        } else {
            if (!pin) throw std::runtime_error("UART TX stop bit is low");
            bytes.push_back(value);
            state = Idle;
        }
    }
};

class Simulation {
    Vtb_soc dut;
    std::unique_ptr<VerilatedVcdC> trace;
    std::ofstream retireLog;
    TxMonitor tx;
    uint64_t timeNs = 0, ticks = 0, retired = 0, irqEntries = 0;
    uint64_t runCycles = 0;
    unsigned pc = 0;
    bool recording = false;

    void evaluate() {
        dut.eval();
        if (trace) trace->dump(timeNs);
        timeNs += kHalfPeriodNs;
        Verilated::timeInc(kHalfPeriodNs);
    }

    void tick() {
        dut.clk = 0;
        evaluate();
        // Retire signals describe the edge about to occur; registers/CSRs
        // describe its result only after that edge has been evaluated.
        const bool valid = recording && dut.retire_valid;
        const unsigned at = dut.retire_pc, instruction = dut.retire_inst;
        const unsigned next = dut.retire_next_pc, irq = dut.retire_irq, ack = dut.irq_ack;
        dut.clk = 1;
        evaluate();
        tx.sample(dut.uart_tx, ++ticks);
        if (valid) {
            ++retired;
            irqEntries += irq;
            pc = next;
            if ((dut.registers[0] & 0xffffu) != 0) throw std::runtime_error("zero register changed");
            if (retireLog.is_open()) {
                retireLog << "{\"pc\":" << at << ",\"inst\":" << instruction
                          << ",\"next_pc\":" << next << ",\"irq\":" << irq
                          << ",\"irq_ack\":" << ack << ",\"registers\":";
                writeWords(retireLog, dut.registers, 8);
                retireLog << ",\"csrs\":";
                writeWords(retireLog, dut.csrs, 6);
                retireLog << ",\"in_interrupt\":" << unsigned(dut.in_interrupt)
                          << ",\"cycle\":" << dut.cycle << "}\n";
            }
        }
        if (Verilated::gotFinish()) throw std::runtime_error("RTL ended simulation before HALT/fault");
    }

    void clocks(unsigned count) { while (count--) tick(); }

    void sendByte(unsigned byte) {
        dut.uart_rx = 0;
        clocks(kBitCycles);
        for (unsigned bit = 0; bit < 8; ++bit) {
            dut.uart_rx = (byte >> bit) & 1;
            clocks(kBitCycles);
        }
        dut.uart_rx = 1;
        clocks(kBitCycles);
    }

public:
    explicit Simulation(const Options& options) {
        dut.clk = 0;
        dut.rst_n = 0;
        dut.uart_rx = 1;
        dut.buttons = options.buttons;
        dut.switches = options.switches;
        dut.probe_address = 0;
        if (!options.trace.empty()) {
            trace.reset(new VerilatedVcdC);
            dut.trace(trace.get(), 99);
            trace->open(options.trace.c_str());
            if (!trace->isOpen()) throw std::runtime_error("cannot open VCD: " + options.trace);
        }
        if (!options.retireLog.empty()) {
            retireLog.open(options.retireLog);
            if (!retireLog) throw std::runtime_error("cannot open retirement log: " + options.retireLog);
        }
        clocks(32); // Allow the UART power-on reset and RX synchronizer to settle.
    }

    ~Simulation() {
        dut.final();
        if (trace) trace->close();
    }

    void program(const std::vector<uint16_t>& image) {
        for (const auto word : image) {
            sendByte(word >> 8);
            sendByte(word & 255);
        }
        clocks(2 * kBitCycles); // The final received pulse must reach ROM storage.
        for (unsigned index = 0; index < image.size(); ++index) {
            dut.probe_address = index;
            dut.eval();
            if (dut.rom_probe != image[index])
                throw std::runtime_error("UART upload/readback mismatch at word " + std::to_string(index));
        }
        dut.probe_address = 0;
        if (dut.retire_valid || dut.halted || dut.faulted)
            throw std::runtime_error("CPU executed while held in programming reset");
    }

    int run(const Options& options) {
        dut.rst_n = 1;
        recording = true;
        while (!dut.halted && !dut.faulted && runCycles < options.maxCycles) {
            // Start runtime RX after software has had 64 cycles to initialize.
            // Queue entries are 8N1 frames plus one idle bit between bytes.
            dut.uart_rx = 1;
            if (runCycles >= 64) {
                const uint64_t offset = runCycles - 64;
                const uint64_t byte = offset / (11 * kBitCycles);
                const unsigned bit = (offset % (11 * kBitCycles)) / kBitCycles;
                if (byte < options.rxBytes.size()) {
                    if (bit == 0) dut.uart_rx = 0;
                    else if (bit <= 8) dut.uart_rx = (options.rxBytes[byte] >> (bit - 1)) & 1;
                }
            }
            tick();
            ++runCycles;
        }
        const int result = dut.faulted ? 2 : dut.halted ? 0 : 3;
        if (dut.faulted) pc = dut.fault_pc;
        if (result == 3) std::cerr << "simulation reached --max-cycles without HALT/fault\n";
        dut.uart_rx = 1;
        // HALT stops the core, not the UART. Let all queued TX bytes finish.
        // On timeout leave the model at the requested limit instead.
        if (result != 3) {
            unsigned budget = 18 * 10 * kBitCycles;
            while ((dut.uart_busy || !tx.idle()) && budget) { tick(); --budget; }
            if (dut.uart_busy || !tx.idle()) throw std::runtime_error("UART TX failed to drain");
        }
        if (retireLog.is_open()) {
            retireLog.flush();
            if (!retireLog) throw std::runtime_error("failed to write retirement log");
        }
        return result;
    }

    void report() {
        std::cout << "{\"halted\":" << unsigned(dut.halted)
                  << ",\"faulted\":" << unsigned(dut.faulted)
                  << ",\"fault_code\":" << unsigned(dut.fault_code)
                  << ",\"fault_pc\":" << dut.fault_pc << ",\"fault_inst\":" << dut.fault_inst
                  << ",\"pc\":" << pc << ",\"cycles\":" << runCycles
                  << ",\"retired\":" << retired << ",\"irq_entries\":" << irqEntries
                  << ",\"in_interrupt\":" << unsigned(dut.in_interrupt) << ",\"registers\":";
        writeWords(std::cout, dut.registers, 8);
        std::cout << ",\"csrs\":";
        writeWords(std::cout, dut.csrs, 6);
        std::cout << ",\"led\":" << unsigned(dut.led)
                  << ",\"digit_enable\":" << unsigned(dut.digit_enable)
                  << ",\"segments\":" << unsigned(dut.segments)
                  << ",\"display_value\":" << dut.display_value << ",\"uart_tx\":[";
        for (unsigned index = 0; index < tx.bytes.size(); ++index) {
            if (index) std::cout << ',';
            std::cout << tx.bytes[index];
        }
        std::cout << "],\"memory\":{";
        bool first = true;
        for (unsigned address = 0; address < kWords; ++address) {
            dut.probe_address = address;
            dut.eval();
            if (dut.ram_probe) {
                if (!first) std::cout << ',';
                first = false;
                std::cout << '\"' << address << "\":" << dut.ram_probe;
            }
        }
        std::cout << "}}\n";
    }
};
} // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Vtb_soc --image FILE [--trace FILE] [--retire-log FILE]\n"
                     "        [--max-cycles N] [--buttons N] [--switches N] [--rx-byte N ...]\n";
        return 0;
    }
    try {
        const auto options = parseOptions(argc, argv);
        const auto image = readImage(options.image);
        Verilated::commandArgs(argc, argv);
        Verilated::traceEverOn(!options.trace.empty());
        Simulation simulation(options);
        simulation.program(image);
        const int result = simulation.run(options);
        simulation.report();
        return result;
    } catch (const std::exception& error) {
        std::cerr << "testbench: " << error.what() << '\n';
        return 1;
    }
}
