; Expected a1 = 17. i1 values remain canonical through PHI, branch and select.
define i16 @main() {
entry:
  br label %loop
loop:
  %condition = phi i1 [ false, %entry ], [ true, %again ]
  br i1 %condition, label %end, label %again
again:
  br label %loop
end:
  %selected = select i1 %condition, i1 false, i1 true
  %value = zext i1 %selected to i16
  %result = add i16 %value, 17
  ret i16 %result
}
