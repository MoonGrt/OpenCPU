; Expected a1 = 32769; valid i16 shift amounts are 0..15 in LLVM IR.
define i16 @shift(i16 %x, i16 %amount) {
  %left = shl i16 %x, %amount
  %right = lshr i16 %left, %amount
  %result = xor i16 %left, %right
  ret i16 %result
}
define i16 @main() {
  %a = call i16 @shift(i16 1, i16 15)
  %b = call i16 @shift(i16 -1, i16 0)
  %result = add i16 %a, %b
  ret i16 %result
}
