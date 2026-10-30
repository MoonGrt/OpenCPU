; Expected a1 = 836. Arguments keep the arithmetic live through code generation.
define i16 @mix(i16 %x, i16 %y) {
entry:
  %a = add i16 %x, %y
  %s = sub i16 %a, 5
  %m = mul i16 %s, %y
  %n = and i16 %m, 255
  %o = or i16 %n, 256
  %q = xor i16 %o, 85
  %l = shl i16 %q, 3
  %r = lshr i16 %l, 2
  ret i16 %r
}

define i16 @main() {
entry:
  %result = call i16 @mix(i16 -1, i16 3)
  ret i16 %result
}
