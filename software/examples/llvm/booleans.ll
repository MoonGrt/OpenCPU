; Expected a1 = 23; true sext is 0xffff, while true zext is 1.
define i16 @boolean_value(i16 %x) {
entry:
  %bit = trunc i16 %x to i1
  %unsigned = zext i1 %bit to i16
  %signed = sext i1 %bit to i16
  %a = add i16 %signed, 7
  %b = mul i16 %unsigned, 10
  %result = add i16 %a, %b
  ret i16 %result
}

define i16 @main() {
entry:
  %odd = call i16 @boolean_value(i16 5)
  %even = call i16 @boolean_value(i16 8)
  %result = add i16 %odd, %even
  ret i16 %result
}
