; Expected a1 = 120; non-leaf recursion must preserve RA and the live n.
define i16 @factorial(i16 %n) {
entry:
  %small = icmp ule i16 %n, 1
  br i1 %small, label %base, label %recursive
base:
  ret i16 1
recursive:
  %previous = sub i16 %n, 1
  %tail = call i16 @factorial(i16 %previous)
  %result = mul i16 %n, %tail
  ret i16 %result
}
define i16 @main() {
  %result = call i16 @factorial(i16 5)
  ret i16 %result
}
