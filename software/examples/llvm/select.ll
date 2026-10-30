; Expected a1 = 65521, the i16 representation of -15.
define i16 @minimum(i16 %x, i16 %y) {
entry:
  %less = icmp slt i16 %x, %y
  %result = select i1 %less, i16 %x, i16 %y
  ret i16 %result
}

define i16 @main() {
entry:
  %a = call i16 @minimum(i16 -5, i16 7)
  %b = call i16 @minimum(i16 100, i16 -10)
  %result = add i16 %a, %b
  ret i16 %result
}
