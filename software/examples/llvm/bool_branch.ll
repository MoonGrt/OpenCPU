; Expected a1 = 13. Trunc to i1 tests the low bit, not whether x is nonzero.
define i16 @low_bit_branch(i16 %x) {
entry:
  %low_bit = trunc i16 %x to i1
  br i1 %low_bit, label %odd, label %even
odd:
  ret i16 11
even:
  ret i16 2
}
define i16 @main() {
  %a = call i16 @low_bit_branch(i16 2)
  %b = call i16 @low_bit_branch(i16 3)
  %result = add i16 %a, %b
  ret i16 %result
}
