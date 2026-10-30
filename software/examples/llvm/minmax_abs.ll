; Expected a1 = 126. Select patterns can become internal min/max/abs DAG nodes.
define i16 @signed_minimum(i16 %a, i16 %b) {
  %condition = icmp slt i16 %a, %b
  %result = select i1 %condition, i16 %a, i16 %b
  ret i16 %result
}
define i16 @signed_maximum(i16 %a, i16 %b) {
  %condition = icmp sgt i16 %a, %b
  %result = select i1 %condition, i16 %a, i16 %b
  ret i16 %result
}
define i16 @unsigned_minimum(i16 %a, i16 %b) {
  %condition = icmp ult i16 %a, %b
  %result = select i1 %condition, i16 %a, i16 %b
  ret i16 %result
}
define i16 @unsigned_maximum(i16 %a, i16 %b) {
  %condition = icmp ugt i16 %a, %b
  %result = select i1 %condition, i16 %a, i16 %b
  ret i16 %result
}
define i16 @absolute(i16 %a) {
  %negative = sub i16 0, %a
  %positive = icmp sgt i16 %a, 0
  %result = select i1 %positive, i16 %a, i16 %negative
  ret i16 %result
}
define i16 @main() {
  %a = call i16 @signed_minimum(i16 -32768, i16 7)
  %b = call i16 @signed_maximum(i16 -1, i16 32767)
  %c = call i16 @absolute(i16 -123)
  %d = call i16 @unsigned_minimum(i16 -1, i16 5)
  %e = call i16 @unsigned_maximum(i16 -1, i16 0)
  %ab = add i16 %a, %b
  %abc = add i16 %ab, %c
  %abcd = add i16 %abc, %d
  %result = add i16 %abcd, %e
  ret i16 %result
}
