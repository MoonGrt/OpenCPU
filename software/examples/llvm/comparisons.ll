; Expected a1 = 3099. Each predicate has its own bit in the result.
define i16 @flags(i16 %x, i16 %y) {
entry:
  %eq = icmp eq i16 %x, %y
  %ne = icmp ne i16 %x, %y
  %ugt = icmp ugt i16 %x, %y
  %uge = icmp uge i16 %x, %y
  %ult = icmp ult i16 %x, %y
  %ule = icmp ule i16 %x, %y
  %sgt = icmp sgt i16 %x, %y
  %sge = icmp sge i16 %x, %y
  %slt = icmp slt i16 %x, %y
  %sle = icmp sle i16 %x, %y
  %b0 = zext i1 %eq to i16
  %v1 = zext i1 %ne to i16
  %v2 = zext i1 %ugt to i16
  %v3 = zext i1 %uge to i16
  %v4 = zext i1 %ult to i16
  %v5 = zext i1 %ule to i16
  %v6 = zext i1 %sgt to i16
  %v7 = zext i1 %sge to i16
  %v8 = zext i1 %slt to i16
  %v9 = zext i1 %sle to i16
  %b1 = shl i16 %v1, 1
  %b2 = shl i16 %v2, 2
  %b3 = shl i16 %v3, 3
  %b4 = shl i16 %v4, 4
  %b5 = shl i16 %v5, 5
  %b6 = shl i16 %v6, 6
  %b7 = shl i16 %v7, 7
  %b8 = shl i16 %v8, 8
  %b9 = shl i16 %v9, 9
  %s1 = or i16 %b0, %b1
  %s2 = or i16 %s1, %b2
  %s3 = or i16 %s2, %b3
  %s4 = or i16 %s3, %b4
  %s5 = or i16 %s4, %b5
  %s6 = or i16 %s5, %b6
  %s7 = or i16 %s6, %b7
  %s8 = or i16 %s7, %b8
  %s9 = or i16 %s8, %b9
  ret i16 %s9
}

define i16 @main() {
entry:
  %a = call i16 @flags(i16 -32768, i16 -1)
  %b = call i16 @flags(i16 0, i16 32767)
  %c = call i16 @flags(i16 -1, i16 0)
  %d = call i16 @flags(i16 32767, i16 32767)
  %ab = add i16 %a, %b
  %cd = add i16 %c, %d
  %result = add i16 %ab, %cd
  ret i16 %result
}
