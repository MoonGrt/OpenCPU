; Expected a1 = 117; eight values stay live across calls with four allocatable GPRs.
define i16 @seed() {
  ret i16 9
}
define i16 @bump(i16 %x) {
  %result = xor i16 %x, 23130
  ret i16 %result
}
define i16 @main() {
  %seed = call i16 @seed()
  %v1 = add i16 %seed, 1
  %v2 = add i16 %seed, 2
  %v3 = add i16 %seed, 3
  %v4 = add i16 %seed, 4
  %v5 = add i16 %seed, 5
  %v6 = add i16 %seed, 6
  %v7 = add i16 %seed, 7
  %v8 = add i16 %seed, 8
  %first = call i16 @bump(i16 %seed)
  %second = call i16 @bump(i16 %first)
  %s1 = add i16 %v1, %v2
  %s2 = add i16 %s1, %v3
  %s3 = add i16 %s2, %v4
  %s4 = add i16 %s3, %v5
  %s5 = add i16 %s4, %v6
  %s6 = add i16 %s5, %v7
  %s7 = add i16 %s6, %v8
  %result = add i16 %s7, %second
  ret i16 %result
}
