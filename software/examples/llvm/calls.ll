; Expected a1 = 133; exercises 0, 1, 2, 3, 4 arguments and void return.
define i16 @zero() {
  ret i16 7
}
define i16 @one(i16 %a) {
  %result = add i16 %a, 1
  ret i16 %result
}
define i16 @two(i16 %a, i16 %b) {
  %result = sub i16 %a, %b
  ret i16 %result
}
define i16 @three(i16 %a, i16 %b, i16 %c) {
  %product = mul i16 %b, %c
  %result = add i16 %a, %product
  ret i16 %result
}
define i16 @four(i16 %a, i16 %b, i16 %c, i16 %d) {
  %left = add i16 %a, %b
  %right = add i16 %c, %d
  %result = mul i16 %left, %right
  ret i16 %result
}
define void @sink(i16 %value) {
  ret void
}
define i16 @main() {
  %a = call i16 @zero()
  %b = call i16 @one(i16 %a)
  %c = call i16 @two(i16 %b, i16 3)
  %d = call i16 @three(i16 %c, i16 4, i16 3)
  %result = call i16 @four(i16 %d, i16 2, i16 5, i16 2)
  call void @sink(i16 %result)
  ret i16 %result
}
