; OpenCPU ABI v2 integer runtime. Arithmetic inside these routines uses
; 16-bit limbs; wider shifts below only unpack/pack constant-position limbs.
target triple = "opencpu-unknown-none"
target datalayout = "e-m:e-p:16:16-i32:16-i64:16-f32:16-f64:16-n16-S16"

define i16 @__opencpu_udiv16(i16 %a, i16 %b) #0 {
entry:
  br label %loop
loop:
  %n0 = phi i16 [ %a, %entry ], [ %nx0, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %q0 = phi i16 [ 0, %entry ], [ %qx0, %step ]
  %count = phi i16 [ 16, %entry ], [ %countx, %step ]
  br label %step
step:
  %v1 = lshr i16 %n0, 15
  %v2 = icmp slt i16 %r0, 0
  %v3 = shl i16 %r0, 1
  %v4 = or i16 %v3, 0
  %v5 = or i16 %v4, %v1
  %v6 = sub i16 %v5, %b
  %v7 = icmp ult i16 %v5, %b
  %v8 = sub i16 %v6, 0
  %v9 = icmp ult i16 %v6, 0
  %v10 = or i1 %v7, %v9
  %v11 = zext i1 %v10 to i16
  %v12 = icmp eq i16 %v11, 0
  %v13 = or i1 %v2, %v12
  %v14 = select i1 %v13, i16 %v8, i16 %v5
  %v15 = shl i16 %q0, 1
  %v16 = or i16 %v15, 0
  %v17 = zext i1 %v13 to i16
  %v18 = or i16 %v16, %v17
  %v19 = shl i16 %n0, 1
  %v20 = or i16 %v19, 0
  %rx0 = add i16 %v14, 0
  %qx0 = add i16 %v18, 0
  %nx0 = add i16 %v20, 0
  %countx = sub i16 %count, 1
  %v21 = icmp eq i16 %countx, 0
  br i1 %v21, label %exit, label %loop
exit:
  ret i16 %v18
}

define i16 @__opencpu_urem16(i16 %a, i16 %b) #0 {
entry:
  br label %loop
loop:
  %n0 = phi i16 [ %a, %entry ], [ %nx0, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %q0 = phi i16 [ 0, %entry ], [ %qx0, %step ]
  %count = phi i16 [ 16, %entry ], [ %countx, %step ]
  br label %step
step:
  %v1 = lshr i16 %n0, 15
  %v2 = icmp slt i16 %r0, 0
  %v3 = shl i16 %r0, 1
  %v4 = or i16 %v3, 0
  %v5 = or i16 %v4, %v1
  %v6 = sub i16 %v5, %b
  %v7 = icmp ult i16 %v5, %b
  %v8 = sub i16 %v6, 0
  %v9 = icmp ult i16 %v6, 0
  %v10 = or i1 %v7, %v9
  %v11 = zext i1 %v10 to i16
  %v12 = icmp eq i16 %v11, 0
  %v13 = or i1 %v2, %v12
  %v14 = select i1 %v13, i16 %v8, i16 %v5
  %v15 = shl i16 %q0, 1
  %v16 = or i16 %v15, 0
  %v17 = zext i1 %v13 to i16
  %v18 = or i16 %v16, %v17
  %v19 = shl i16 %n0, 1
  %v20 = or i16 %v19, 0
  %rx0 = add i16 %v14, 0
  %qx0 = add i16 %v18, 0
  %nx0 = add i16 %v20, 0
  %countx = sub i16 %count, 1
  %v21 = icmp eq i16 %countx, 0
  br i1 %v21, label %exit, label %loop
exit:
  ret i16 %v14
}

define i16 @__opencpu_sdiv16(i16 %a, i16 %b) #0 {
entry:
  %v1 = icmp slt i16 %a, 0
  br i1 %v1, label %aneg, label %ajoin
aneg:
  %v2 = sub i16 0, %a
  %v3 = sub i16 %v2, 0
  %v4 = icmp ne i16 %a, 0
  %v5 = zext i1 %v4 to i16
  %v6 = or i16 %v5, 0
  br label %ajoin
ajoin:
  %v7 = phi i16 [ %a, %entry ], [ %v3, %aneg ]
  %v8 = icmp slt i16 %b, 0
  br i1 %v8, label %bneg, label %bjoin
bneg:
  %v9 = sub i16 0, %b
  %v10 = sub i16 %v9, 0
  %v11 = icmp ne i16 %b, 0
  %v12 = zext i1 %v11 to i16
  %v13 = or i16 %v12, 0
  br label %bjoin
bjoin:
  %v14 = phi i16 [ %b, %ajoin ], [ %v10, %bneg ]
  %v15 = call i16 @__opencpu_udiv16(i16 %v7, i16 %v14)
  %v16 = xor i1 %v1, %v8
  br i1 %v16, label %resultneg, label %resultjoin
resultneg:
  %v17 = sub i16 0, %v15
  %v18 = sub i16 %v17, 0
  %v19 = icmp ne i16 %v15, 0
  %v20 = zext i1 %v19 to i16
  %v21 = or i16 %v20, 0
  br label %resultjoin
resultjoin:
  %v22 = phi i16 [ %v15, %bjoin ], [ %v18, %resultneg ]
  ret i16 %v22
}

define i16 @__opencpu_srem16(i16 %a, i16 %b) #0 {
entry:
  %v1 = icmp slt i16 %a, 0
  br i1 %v1, label %aneg, label %ajoin
aneg:
  %v2 = sub i16 0, %a
  %v3 = sub i16 %v2, 0
  %v4 = icmp ne i16 %a, 0
  %v5 = zext i1 %v4 to i16
  %v6 = or i16 %v5, 0
  br label %ajoin
ajoin:
  %v7 = phi i16 [ %a, %entry ], [ %v3, %aneg ]
  %v8 = icmp slt i16 %b, 0
  br i1 %v8, label %bneg, label %bjoin
bneg:
  %v9 = sub i16 0, %b
  %v10 = sub i16 %v9, 0
  %v11 = icmp ne i16 %b, 0
  %v12 = zext i1 %v11 to i16
  %v13 = or i16 %v12, 0
  br label %bjoin
bjoin:
  %v14 = phi i16 [ %b, %ajoin ], [ %v10, %bneg ]
  %v15 = call i16 @__opencpu_urem16(i16 %v7, i16 %v14)
  br i1 %v1, label %resultneg, label %resultjoin
resultneg:
  %v16 = sub i16 0, %v15
  %v17 = sub i16 %v16, 0
  %v18 = icmp ne i16 %v15, 0
  %v19 = zext i1 %v18 to i16
  %v20 = or i16 %v19, 0
  br label %resultjoin
resultjoin:
  %v21 = phi i16 [ %v15, %bjoin ], [ %v17, %resultneg ]
  ret i16 %v21
}

define i32 @__opencpu_udiv32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  %v5 = lshr i32 %b, 16
  %v6 = trunc i32 %v5 to i16
  br label %loop
loop:
  %n0 = phi i16 [ %v1, %entry ], [ %nx0, %step ]
  %n1 = phi i16 [ %v3, %entry ], [ %nx1, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %r1 = phi i16 [ 0, %entry ], [ %rx1, %step ]
  %q0 = phi i16 [ 0, %entry ], [ %qx0, %step ]
  %q1 = phi i16 [ 0, %entry ], [ %qx1, %step ]
  %count = phi i16 [ 32, %entry ], [ %countx, %step ]
  br label %step
step:
  %v7 = lshr i16 %n1, 15
  %v8 = icmp slt i16 %r1, 0
  %v9 = shl i16 %r0, 1
  %v10 = or i16 %v9, 0
  %v11 = shl i16 %r1, 1
  %v12 = lshr i16 %r0, 15
  %v13 = or i16 %v11, %v12
  %v14 = or i16 %v10, %v7
  %v15 = sub i16 %v14, %v4
  %v16 = icmp ult i16 %v14, %v4
  %v17 = sub i16 %v15, 0
  %v18 = icmp ult i16 %v15, 0
  %v19 = or i1 %v16, %v18
  %v20 = zext i1 %v19 to i16
  %v21 = sub i16 %v13, %v6
  %v22 = icmp ult i16 %v13, %v6
  %v23 = sub i16 %v21, %v20
  %v24 = icmp ult i16 %v21, %v20
  %v25 = or i1 %v22, %v24
  %v26 = zext i1 %v25 to i16
  %v27 = icmp eq i16 %v26, 0
  %v28 = or i1 %v8, %v27
  %v29 = select i1 %v28, i16 %v17, i16 %v14
  %v30 = select i1 %v28, i16 %v23, i16 %v13
  %v31 = shl i16 %q0, 1
  %v32 = or i16 %v31, 0
  %v33 = shl i16 %q1, 1
  %v34 = lshr i16 %q0, 15
  %v35 = or i16 %v33, %v34
  %v36 = zext i1 %v28 to i16
  %v37 = or i16 %v32, %v36
  %v38 = shl i16 %n0, 1
  %v39 = or i16 %v38, 0
  %v40 = shl i16 %n1, 1
  %v41 = lshr i16 %n0, 15
  %v42 = or i16 %v40, %v41
  %rx0 = add i16 %v29, 0
  %qx0 = add i16 %v37, 0
  %nx0 = add i16 %v39, 0
  %rx1 = add i16 %v30, 0
  %qx1 = add i16 %v35, 0
  %nx1 = add i16 %v42, 0
  %countx = sub i16 %count, 1
  %v43 = icmp eq i16 %countx, 0
  br i1 %v43, label %exit, label %loop
exit:
  %v44 = zext i16 %v37 to i32
  %v45 = zext i16 %v35 to i32
  %v46 = shl i32 %v45, 16
  %v47 = or i32 %v44, %v46
  ret i32 %v47
}

define i32 @__opencpu_urem32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  %v5 = lshr i32 %b, 16
  %v6 = trunc i32 %v5 to i16
  br label %loop
loop:
  %n0 = phi i16 [ %v1, %entry ], [ %nx0, %step ]
  %n1 = phi i16 [ %v3, %entry ], [ %nx1, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %r1 = phi i16 [ 0, %entry ], [ %rx1, %step ]
  %q0 = phi i16 [ 0, %entry ], [ %qx0, %step ]
  %q1 = phi i16 [ 0, %entry ], [ %qx1, %step ]
  %count = phi i16 [ 32, %entry ], [ %countx, %step ]
  br label %step
step:
  %v7 = lshr i16 %n1, 15
  %v8 = icmp slt i16 %r1, 0
  %v9 = shl i16 %r0, 1
  %v10 = or i16 %v9, 0
  %v11 = shl i16 %r1, 1
  %v12 = lshr i16 %r0, 15
  %v13 = or i16 %v11, %v12
  %v14 = or i16 %v10, %v7
  %v15 = sub i16 %v14, %v4
  %v16 = icmp ult i16 %v14, %v4
  %v17 = sub i16 %v15, 0
  %v18 = icmp ult i16 %v15, 0
  %v19 = or i1 %v16, %v18
  %v20 = zext i1 %v19 to i16
  %v21 = sub i16 %v13, %v6
  %v22 = icmp ult i16 %v13, %v6
  %v23 = sub i16 %v21, %v20
  %v24 = icmp ult i16 %v21, %v20
  %v25 = or i1 %v22, %v24
  %v26 = zext i1 %v25 to i16
  %v27 = icmp eq i16 %v26, 0
  %v28 = or i1 %v8, %v27
  %v29 = select i1 %v28, i16 %v17, i16 %v14
  %v30 = select i1 %v28, i16 %v23, i16 %v13
  %v31 = shl i16 %q0, 1
  %v32 = or i16 %v31, 0
  %v33 = shl i16 %q1, 1
  %v34 = lshr i16 %q0, 15
  %v35 = or i16 %v33, %v34
  %v36 = zext i1 %v28 to i16
  %v37 = or i16 %v32, %v36
  %v38 = shl i16 %n0, 1
  %v39 = or i16 %v38, 0
  %v40 = shl i16 %n1, 1
  %v41 = lshr i16 %n0, 15
  %v42 = or i16 %v40, %v41
  %rx0 = add i16 %v29, 0
  %qx0 = add i16 %v37, 0
  %nx0 = add i16 %v39, 0
  %rx1 = add i16 %v30, 0
  %qx1 = add i16 %v35, 0
  %nx1 = add i16 %v42, 0
  %countx = sub i16 %count, 1
  %v43 = icmp eq i16 %countx, 0
  br i1 %v43, label %exit, label %loop
exit:
  %v44 = zext i16 %v29 to i32
  %v45 = zext i16 %v30 to i32
  %v46 = shl i32 %v45, 16
  %v47 = or i32 %v44, %v46
  ret i32 %v47
}

define i32 @__opencpu_sdiv32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  %v5 = lshr i32 %b, 16
  %v6 = trunc i32 %v5 to i16
  %v7 = icmp slt i16 %v3, 0
  br i1 %v7, label %aneg, label %ajoin
aneg:
  %v8 = sub i16 0, %v1
  %v9 = sub i16 %v8, 0
  %v10 = icmp ne i16 %v1, 0
  %v11 = zext i1 %v10 to i16
  %v12 = or i16 %v11, 0
  %v13 = sub i16 0, %v3
  %v14 = sub i16 %v13, %v12
  %v15 = icmp ne i16 %v3, 0
  %v16 = zext i1 %v15 to i16
  %v17 = or i16 %v16, %v12
  br label %ajoin
ajoin:
  %v18 = phi i16 [ %v1, %entry ], [ %v9, %aneg ]
  %v19 = phi i16 [ %v3, %entry ], [ %v14, %aneg ]
  %v20 = icmp slt i16 %v6, 0
  br i1 %v20, label %bneg, label %bjoin
bneg:
  %v21 = sub i16 0, %v4
  %v22 = sub i16 %v21, 0
  %v23 = icmp ne i16 %v4, 0
  %v24 = zext i1 %v23 to i16
  %v25 = or i16 %v24, 0
  %v26 = sub i16 0, %v6
  %v27 = sub i16 %v26, %v25
  %v28 = icmp ne i16 %v6, 0
  %v29 = zext i1 %v28 to i16
  %v30 = or i16 %v29, %v25
  br label %bjoin
bjoin:
  %v31 = phi i16 [ %v4, %ajoin ], [ %v22, %bneg ]
  %v32 = phi i16 [ %v6, %ajoin ], [ %v27, %bneg ]
  %v33 = zext i16 %v18 to i32
  %v34 = zext i16 %v19 to i32
  %v35 = shl i32 %v34, 16
  %v36 = or i32 %v33, %v35
  %v37 = zext i16 %v31 to i32
  %v38 = zext i16 %v32 to i32
  %v39 = shl i32 %v38, 16
  %v40 = or i32 %v37, %v39
  %v41 = call i32 @__opencpu_udiv32(i32 %v36, i32 %v40)
  %v42 = trunc i32 %v41 to i16
  %v43 = lshr i32 %v41, 16
  %v44 = trunc i32 %v43 to i16
  %v45 = xor i1 %v7, %v20
  br i1 %v45, label %resultneg, label %resultjoin
resultneg:
  %v46 = sub i16 0, %v42
  %v47 = sub i16 %v46, 0
  %v48 = icmp ne i16 %v42, 0
  %v49 = zext i1 %v48 to i16
  %v50 = or i16 %v49, 0
  %v51 = sub i16 0, %v44
  %v52 = sub i16 %v51, %v50
  %v53 = icmp ne i16 %v44, 0
  %v54 = zext i1 %v53 to i16
  %v55 = or i16 %v54, %v50
  br label %resultjoin
resultjoin:
  %v56 = phi i16 [ %v42, %bjoin ], [ %v47, %resultneg ]
  %v57 = phi i16 [ %v44, %bjoin ], [ %v52, %resultneg ]
  %v58 = zext i16 %v56 to i32
  %v59 = zext i16 %v57 to i32
  %v60 = shl i32 %v59, 16
  %v61 = or i32 %v58, %v60
  ret i32 %v61
}

define i32 @__opencpu_srem32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  %v5 = lshr i32 %b, 16
  %v6 = trunc i32 %v5 to i16
  %v7 = icmp slt i16 %v3, 0
  br i1 %v7, label %aneg, label %ajoin
aneg:
  %v8 = sub i16 0, %v1
  %v9 = sub i16 %v8, 0
  %v10 = icmp ne i16 %v1, 0
  %v11 = zext i1 %v10 to i16
  %v12 = or i16 %v11, 0
  %v13 = sub i16 0, %v3
  %v14 = sub i16 %v13, %v12
  %v15 = icmp ne i16 %v3, 0
  %v16 = zext i1 %v15 to i16
  %v17 = or i16 %v16, %v12
  br label %ajoin
ajoin:
  %v18 = phi i16 [ %v1, %entry ], [ %v9, %aneg ]
  %v19 = phi i16 [ %v3, %entry ], [ %v14, %aneg ]
  %v20 = icmp slt i16 %v6, 0
  br i1 %v20, label %bneg, label %bjoin
bneg:
  %v21 = sub i16 0, %v4
  %v22 = sub i16 %v21, 0
  %v23 = icmp ne i16 %v4, 0
  %v24 = zext i1 %v23 to i16
  %v25 = or i16 %v24, 0
  %v26 = sub i16 0, %v6
  %v27 = sub i16 %v26, %v25
  %v28 = icmp ne i16 %v6, 0
  %v29 = zext i1 %v28 to i16
  %v30 = or i16 %v29, %v25
  br label %bjoin
bjoin:
  %v31 = phi i16 [ %v4, %ajoin ], [ %v22, %bneg ]
  %v32 = phi i16 [ %v6, %ajoin ], [ %v27, %bneg ]
  %v33 = zext i16 %v18 to i32
  %v34 = zext i16 %v19 to i32
  %v35 = shl i32 %v34, 16
  %v36 = or i32 %v33, %v35
  %v37 = zext i16 %v31 to i32
  %v38 = zext i16 %v32 to i32
  %v39 = shl i32 %v38, 16
  %v40 = or i32 %v37, %v39
  %v41 = call i32 @__opencpu_urem32(i32 %v36, i32 %v40)
  %v42 = trunc i32 %v41 to i16
  %v43 = lshr i32 %v41, 16
  %v44 = trunc i32 %v43 to i16
  br i1 %v7, label %resultneg, label %resultjoin
resultneg:
  %v45 = sub i16 0, %v42
  %v46 = sub i16 %v45, 0
  %v47 = icmp ne i16 %v42, 0
  %v48 = zext i1 %v47 to i16
  %v49 = or i16 %v48, 0
  %v50 = sub i16 0, %v44
  %v51 = sub i16 %v50, %v49
  %v52 = icmp ne i16 %v44, 0
  %v53 = zext i1 %v52 to i16
  %v54 = or i16 %v53, %v49
  br label %resultjoin
resultjoin:
  %v55 = phi i16 [ %v42, %bjoin ], [ %v46, %resultneg ]
  %v56 = phi i16 [ %v44, %bjoin ], [ %v51, %resultneg ]
  %v57 = zext i16 %v55 to i32
  %v58 = zext i16 %v56 to i32
  %v59 = shl i32 %v58, 16
  %v60 = or i32 %v57, %v59
  ret i32 %v60
}

define i32 @__opencpu_mul32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  %v5 = lshr i32 %b, 16
  %v6 = trunc i32 %v5 to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %b0 = phi i16 [ %v4, %entry ], [ %bx0, %step ]
  %b1 = phi i16 [ %v6, %entry ], [ %bx1, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %r1 = phi i16 [ 0, %entry ], [ %rx1, %step ]
  %count = phi i16 [ 32, %entry ], [ %countx, %step ]
  br label %step
step:
  %v7 = and i16 %b0, 1
  %v8 = sub i16 0, %v7
  %v9 = and i16 %a0, %v8
  %v10 = add i16 %r0, %v9
  %v11 = icmp ult i16 %v10, %r0
  %v12 = add i16 %v10, 0
  %v13 = icmp ult i16 %v12, %v10
  %v14 = or i1 %v11, %v13
  %v15 = zext i1 %v14 to i16
  %v16 = and i16 %a1, %v8
  %v17 = add i16 %r1, %v16
  %v18 = icmp ult i16 %v17, %r1
  %v19 = add i16 %v17, %v15
  %v20 = icmp ult i16 %v19, %v17
  %v21 = or i1 %v18, %v20
  %v22 = zext i1 %v21 to i16
  %v23 = shl i16 %a0, 1
  %v24 = or i16 %v23, 0
  %v25 = shl i16 %a1, 1
  %v26 = lshr i16 %a0, 15
  %v27 = or i16 %v25, %v26
  %v28 = lshr i16 %b0, 1
  %v29 = shl i16 %b1, 15
  %v30 = or i16 %v28, %v29
  %v31 = lshr i16 %b1, 1
  %v32 = or i16 %v31, 0
  %ax0 = add i16 %v24, 0
  %bx0 = add i16 %v30, 0
  %rx0 = add i16 %v12, 0
  %ax1 = add i16 %v27, 0
  %bx1 = add i16 %v32, 0
  %rx1 = add i16 %v19, 0
  %countx = sub i16 %count, 1
  %v33 = icmp eq i16 %countx, 0
  br i1 %v33, label %exit, label %loop
exit:
  %v34 = zext i16 %v12 to i32
  %v35 = zext i16 %v19 to i32
  %v36 = shl i32 %v35, 16
  %v37 = or i32 %v34, %v36
  ret i32 %v37
}

define i32 @__opencpu_shl32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %count = phi i16 [ %v4, %entry ], [ %countx, %step ]
  %v5 = icmp eq i16 %count, 0
  br i1 %v5, label %exit, label %step
step:
  %v6 = shl i16 %a0, 1
  %v7 = or i16 %v6, 0
  %v8 = shl i16 %a1, 1
  %v9 = lshr i16 %a0, 15
  %v10 = or i16 %v8, %v9
  %ax0 = add i16 %v7, 0
  %ax1 = add i16 %v10, 0
  %countx = sub i16 %count, 1
  br label %loop
exit:
  %v11 = zext i16 %a0 to i32
  %v12 = zext i16 %a1 to i32
  %v13 = shl i32 %v12, 16
  %v14 = or i32 %v11, %v13
  ret i32 %v14
}

define i32 @__opencpu_lshr32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %count = phi i16 [ %v4, %entry ], [ %countx, %step ]
  %v5 = icmp eq i16 %count, 0
  br i1 %v5, label %exit, label %step
step:
  %v6 = lshr i16 %a0, 1
  %v7 = shl i16 %a1, 15
  %v8 = or i16 %v6, %v7
  %v9 = lshr i16 %a1, 1
  %v10 = or i16 %v9, 0
  %ax0 = add i16 %v8, 0
  %ax1 = add i16 %v10, 0
  %countx = sub i16 %count, 1
  br label %loop
exit:
  %v11 = zext i16 %a0 to i32
  %v12 = zext i16 %a1 to i32
  %v13 = shl i32 %v12, 16
  %v14 = or i32 %v11, %v13
  ret i32 %v14
}

define i32 @__opencpu_ashr32(i32 %a, i32 %b) #0 {
entry:
  %v1 = trunc i32 %a to i16
  %v2 = lshr i32 %a, 16
  %v3 = trunc i32 %v2 to i16
  %v4 = trunc i32 %b to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %count = phi i16 [ %v4, %entry ], [ %countx, %step ]
  %v5 = icmp eq i16 %count, 0
  br i1 %v5, label %exit, label %step
step:
  %v6 = lshr i16 %a0, 1
  %v7 = shl i16 %a1, 15
  %v8 = or i16 %v6, %v7
  %v9 = lshr i16 %a1, 1
  %v10 = and i16 %a1, -32768
  %v11 = or i16 %v9, %v10
  %ax0 = add i16 %v8, 0
  %ax1 = add i16 %v11, 0
  %countx = sub i16 %count, 1
  br label %loop
exit:
  %v12 = zext i16 %a0 to i32
  %v13 = zext i16 %a1 to i32
  %v14 = shl i32 %v13, 16
  %v15 = or i32 %v12, %v14
  ret i32 %v15
}

define i64 @__opencpu_udiv64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  %v9 = lshr i64 %b, 16
  %v10 = trunc i64 %v9 to i16
  %v11 = lshr i64 %b, 32
  %v12 = trunc i64 %v11 to i16
  %v13 = lshr i64 %b, 48
  %v14 = trunc i64 %v13 to i16
  br label %loop
loop:
  %n0 = phi i16 [ %v1, %entry ], [ %nx0, %step ]
  %n1 = phi i16 [ %v3, %entry ], [ %nx1, %step ]
  %n2 = phi i16 [ %v5, %entry ], [ %nx2, %step ]
  %n3 = phi i16 [ %v7, %entry ], [ %nx3, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %r1 = phi i16 [ 0, %entry ], [ %rx1, %step ]
  %r2 = phi i16 [ 0, %entry ], [ %rx2, %step ]
  %r3 = phi i16 [ 0, %entry ], [ %rx3, %step ]
  %q0 = phi i16 [ 0, %entry ], [ %qx0, %step ]
  %q1 = phi i16 [ 0, %entry ], [ %qx1, %step ]
  %q2 = phi i16 [ 0, %entry ], [ %qx2, %step ]
  %q3 = phi i16 [ 0, %entry ], [ %qx3, %step ]
  %count = phi i16 [ 64, %entry ], [ %countx, %step ]
  br label %step
step:
  %v15 = lshr i16 %n3, 15
  %v16 = icmp slt i16 %r3, 0
  %v17 = shl i16 %r0, 1
  %v18 = or i16 %v17, 0
  %v19 = shl i16 %r1, 1
  %v20 = lshr i16 %r0, 15
  %v21 = or i16 %v19, %v20
  %v22 = shl i16 %r2, 1
  %v23 = lshr i16 %r1, 15
  %v24 = or i16 %v22, %v23
  %v25 = shl i16 %r3, 1
  %v26 = lshr i16 %r2, 15
  %v27 = or i16 %v25, %v26
  %v28 = or i16 %v18, %v15
  %v29 = sub i16 %v28, %v8
  %v30 = icmp ult i16 %v28, %v8
  %v31 = sub i16 %v29, 0
  %v32 = icmp ult i16 %v29, 0
  %v33 = or i1 %v30, %v32
  %v34 = zext i1 %v33 to i16
  %v35 = sub i16 %v21, %v10
  %v36 = icmp ult i16 %v21, %v10
  %v37 = sub i16 %v35, %v34
  %v38 = icmp ult i16 %v35, %v34
  %v39 = or i1 %v36, %v38
  %v40 = zext i1 %v39 to i16
  %v41 = sub i16 %v24, %v12
  %v42 = icmp ult i16 %v24, %v12
  %v43 = sub i16 %v41, %v40
  %v44 = icmp ult i16 %v41, %v40
  %v45 = or i1 %v42, %v44
  %v46 = zext i1 %v45 to i16
  %v47 = sub i16 %v27, %v14
  %v48 = icmp ult i16 %v27, %v14
  %v49 = sub i16 %v47, %v46
  %v50 = icmp ult i16 %v47, %v46
  %v51 = or i1 %v48, %v50
  %v52 = zext i1 %v51 to i16
  %v53 = icmp eq i16 %v52, 0
  %v54 = or i1 %v16, %v53
  %v55 = select i1 %v54, i16 %v31, i16 %v28
  %v56 = select i1 %v54, i16 %v37, i16 %v21
  %v57 = select i1 %v54, i16 %v43, i16 %v24
  %v58 = select i1 %v54, i16 %v49, i16 %v27
  %v59 = shl i16 %q0, 1
  %v60 = or i16 %v59, 0
  %v61 = shl i16 %q1, 1
  %v62 = lshr i16 %q0, 15
  %v63 = or i16 %v61, %v62
  %v64 = shl i16 %q2, 1
  %v65 = lshr i16 %q1, 15
  %v66 = or i16 %v64, %v65
  %v67 = shl i16 %q3, 1
  %v68 = lshr i16 %q2, 15
  %v69 = or i16 %v67, %v68
  %v70 = zext i1 %v54 to i16
  %v71 = or i16 %v60, %v70
  %v72 = shl i16 %n0, 1
  %v73 = or i16 %v72, 0
  %v74 = shl i16 %n1, 1
  %v75 = lshr i16 %n0, 15
  %v76 = or i16 %v74, %v75
  %v77 = shl i16 %n2, 1
  %v78 = lshr i16 %n1, 15
  %v79 = or i16 %v77, %v78
  %v80 = shl i16 %n3, 1
  %v81 = lshr i16 %n2, 15
  %v82 = or i16 %v80, %v81
  %rx0 = add i16 %v55, 0
  %qx0 = add i16 %v71, 0
  %nx0 = add i16 %v73, 0
  %rx1 = add i16 %v56, 0
  %qx1 = add i16 %v63, 0
  %nx1 = add i16 %v76, 0
  %rx2 = add i16 %v57, 0
  %qx2 = add i16 %v66, 0
  %nx2 = add i16 %v79, 0
  %rx3 = add i16 %v58, 0
  %qx3 = add i16 %v69, 0
  %nx3 = add i16 %v82, 0
  %countx = sub i16 %count, 1
  %v83 = icmp eq i16 %countx, 0
  br i1 %v83, label %exit, label %loop
exit:
  %v84 = zext i16 %v71 to i64
  %v85 = zext i16 %v63 to i64
  %v86 = shl i64 %v85, 16
  %v87 = or i64 %v84, %v86
  %v88 = zext i16 %v66 to i64
  %v89 = shl i64 %v88, 32
  %v90 = or i64 %v87, %v89
  %v91 = zext i16 %v69 to i64
  %v92 = shl i64 %v91, 48
  %v93 = or i64 %v90, %v92
  ret i64 %v93
}

define i64 @__opencpu_urem64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  %v9 = lshr i64 %b, 16
  %v10 = trunc i64 %v9 to i16
  %v11 = lshr i64 %b, 32
  %v12 = trunc i64 %v11 to i16
  %v13 = lshr i64 %b, 48
  %v14 = trunc i64 %v13 to i16
  br label %loop
loop:
  %n0 = phi i16 [ %v1, %entry ], [ %nx0, %step ]
  %n1 = phi i16 [ %v3, %entry ], [ %nx1, %step ]
  %n2 = phi i16 [ %v5, %entry ], [ %nx2, %step ]
  %n3 = phi i16 [ %v7, %entry ], [ %nx3, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %r1 = phi i16 [ 0, %entry ], [ %rx1, %step ]
  %r2 = phi i16 [ 0, %entry ], [ %rx2, %step ]
  %r3 = phi i16 [ 0, %entry ], [ %rx3, %step ]
  %q0 = phi i16 [ 0, %entry ], [ %qx0, %step ]
  %q1 = phi i16 [ 0, %entry ], [ %qx1, %step ]
  %q2 = phi i16 [ 0, %entry ], [ %qx2, %step ]
  %q3 = phi i16 [ 0, %entry ], [ %qx3, %step ]
  %count = phi i16 [ 64, %entry ], [ %countx, %step ]
  br label %step
step:
  %v15 = lshr i16 %n3, 15
  %v16 = icmp slt i16 %r3, 0
  %v17 = shl i16 %r0, 1
  %v18 = or i16 %v17, 0
  %v19 = shl i16 %r1, 1
  %v20 = lshr i16 %r0, 15
  %v21 = or i16 %v19, %v20
  %v22 = shl i16 %r2, 1
  %v23 = lshr i16 %r1, 15
  %v24 = or i16 %v22, %v23
  %v25 = shl i16 %r3, 1
  %v26 = lshr i16 %r2, 15
  %v27 = or i16 %v25, %v26
  %v28 = or i16 %v18, %v15
  %v29 = sub i16 %v28, %v8
  %v30 = icmp ult i16 %v28, %v8
  %v31 = sub i16 %v29, 0
  %v32 = icmp ult i16 %v29, 0
  %v33 = or i1 %v30, %v32
  %v34 = zext i1 %v33 to i16
  %v35 = sub i16 %v21, %v10
  %v36 = icmp ult i16 %v21, %v10
  %v37 = sub i16 %v35, %v34
  %v38 = icmp ult i16 %v35, %v34
  %v39 = or i1 %v36, %v38
  %v40 = zext i1 %v39 to i16
  %v41 = sub i16 %v24, %v12
  %v42 = icmp ult i16 %v24, %v12
  %v43 = sub i16 %v41, %v40
  %v44 = icmp ult i16 %v41, %v40
  %v45 = or i1 %v42, %v44
  %v46 = zext i1 %v45 to i16
  %v47 = sub i16 %v27, %v14
  %v48 = icmp ult i16 %v27, %v14
  %v49 = sub i16 %v47, %v46
  %v50 = icmp ult i16 %v47, %v46
  %v51 = or i1 %v48, %v50
  %v52 = zext i1 %v51 to i16
  %v53 = icmp eq i16 %v52, 0
  %v54 = or i1 %v16, %v53
  %v55 = select i1 %v54, i16 %v31, i16 %v28
  %v56 = select i1 %v54, i16 %v37, i16 %v21
  %v57 = select i1 %v54, i16 %v43, i16 %v24
  %v58 = select i1 %v54, i16 %v49, i16 %v27
  %v59 = shl i16 %q0, 1
  %v60 = or i16 %v59, 0
  %v61 = shl i16 %q1, 1
  %v62 = lshr i16 %q0, 15
  %v63 = or i16 %v61, %v62
  %v64 = shl i16 %q2, 1
  %v65 = lshr i16 %q1, 15
  %v66 = or i16 %v64, %v65
  %v67 = shl i16 %q3, 1
  %v68 = lshr i16 %q2, 15
  %v69 = or i16 %v67, %v68
  %v70 = zext i1 %v54 to i16
  %v71 = or i16 %v60, %v70
  %v72 = shl i16 %n0, 1
  %v73 = or i16 %v72, 0
  %v74 = shl i16 %n1, 1
  %v75 = lshr i16 %n0, 15
  %v76 = or i16 %v74, %v75
  %v77 = shl i16 %n2, 1
  %v78 = lshr i16 %n1, 15
  %v79 = or i16 %v77, %v78
  %v80 = shl i16 %n3, 1
  %v81 = lshr i16 %n2, 15
  %v82 = or i16 %v80, %v81
  %rx0 = add i16 %v55, 0
  %qx0 = add i16 %v71, 0
  %nx0 = add i16 %v73, 0
  %rx1 = add i16 %v56, 0
  %qx1 = add i16 %v63, 0
  %nx1 = add i16 %v76, 0
  %rx2 = add i16 %v57, 0
  %qx2 = add i16 %v66, 0
  %nx2 = add i16 %v79, 0
  %rx3 = add i16 %v58, 0
  %qx3 = add i16 %v69, 0
  %nx3 = add i16 %v82, 0
  %countx = sub i16 %count, 1
  %v83 = icmp eq i16 %countx, 0
  br i1 %v83, label %exit, label %loop
exit:
  %v84 = zext i16 %v55 to i64
  %v85 = zext i16 %v56 to i64
  %v86 = shl i64 %v85, 16
  %v87 = or i64 %v84, %v86
  %v88 = zext i16 %v57 to i64
  %v89 = shl i64 %v88, 32
  %v90 = or i64 %v87, %v89
  %v91 = zext i16 %v58 to i64
  %v92 = shl i64 %v91, 48
  %v93 = or i64 %v90, %v92
  ret i64 %v93
}

define i64 @__opencpu_sdiv64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  %v9 = lshr i64 %b, 16
  %v10 = trunc i64 %v9 to i16
  %v11 = lshr i64 %b, 32
  %v12 = trunc i64 %v11 to i16
  %v13 = lshr i64 %b, 48
  %v14 = trunc i64 %v13 to i16
  %v15 = icmp slt i16 %v7, 0
  br i1 %v15, label %aneg, label %ajoin
aneg:
  %v16 = sub i16 0, %v1
  %v17 = sub i16 %v16, 0
  %v18 = icmp ne i16 %v1, 0
  %v19 = zext i1 %v18 to i16
  %v20 = or i16 %v19, 0
  %v21 = sub i16 0, %v3
  %v22 = sub i16 %v21, %v20
  %v23 = icmp ne i16 %v3, 0
  %v24 = zext i1 %v23 to i16
  %v25 = or i16 %v24, %v20
  %v26 = sub i16 0, %v5
  %v27 = sub i16 %v26, %v25
  %v28 = icmp ne i16 %v5, 0
  %v29 = zext i1 %v28 to i16
  %v30 = or i16 %v29, %v25
  %v31 = sub i16 0, %v7
  %v32 = sub i16 %v31, %v30
  %v33 = icmp ne i16 %v7, 0
  %v34 = zext i1 %v33 to i16
  %v35 = or i16 %v34, %v30
  br label %ajoin
ajoin:
  %v36 = phi i16 [ %v1, %entry ], [ %v17, %aneg ]
  %v37 = phi i16 [ %v3, %entry ], [ %v22, %aneg ]
  %v38 = phi i16 [ %v5, %entry ], [ %v27, %aneg ]
  %v39 = phi i16 [ %v7, %entry ], [ %v32, %aneg ]
  %v40 = icmp slt i16 %v14, 0
  br i1 %v40, label %bneg, label %bjoin
bneg:
  %v41 = sub i16 0, %v8
  %v42 = sub i16 %v41, 0
  %v43 = icmp ne i16 %v8, 0
  %v44 = zext i1 %v43 to i16
  %v45 = or i16 %v44, 0
  %v46 = sub i16 0, %v10
  %v47 = sub i16 %v46, %v45
  %v48 = icmp ne i16 %v10, 0
  %v49 = zext i1 %v48 to i16
  %v50 = or i16 %v49, %v45
  %v51 = sub i16 0, %v12
  %v52 = sub i16 %v51, %v50
  %v53 = icmp ne i16 %v12, 0
  %v54 = zext i1 %v53 to i16
  %v55 = or i16 %v54, %v50
  %v56 = sub i16 0, %v14
  %v57 = sub i16 %v56, %v55
  %v58 = icmp ne i16 %v14, 0
  %v59 = zext i1 %v58 to i16
  %v60 = or i16 %v59, %v55
  br label %bjoin
bjoin:
  %v61 = phi i16 [ %v8, %ajoin ], [ %v42, %bneg ]
  %v62 = phi i16 [ %v10, %ajoin ], [ %v47, %bneg ]
  %v63 = phi i16 [ %v12, %ajoin ], [ %v52, %bneg ]
  %v64 = phi i16 [ %v14, %ajoin ], [ %v57, %bneg ]
  %v65 = zext i16 %v36 to i64
  %v66 = zext i16 %v37 to i64
  %v67 = shl i64 %v66, 16
  %v68 = or i64 %v65, %v67
  %v69 = zext i16 %v38 to i64
  %v70 = shl i64 %v69, 32
  %v71 = or i64 %v68, %v70
  %v72 = zext i16 %v39 to i64
  %v73 = shl i64 %v72, 48
  %v74 = or i64 %v71, %v73
  %v75 = zext i16 %v61 to i64
  %v76 = zext i16 %v62 to i64
  %v77 = shl i64 %v76, 16
  %v78 = or i64 %v75, %v77
  %v79 = zext i16 %v63 to i64
  %v80 = shl i64 %v79, 32
  %v81 = or i64 %v78, %v80
  %v82 = zext i16 %v64 to i64
  %v83 = shl i64 %v82, 48
  %v84 = or i64 %v81, %v83
  %v85 = call i64 @__opencpu_udiv64(i64 %v74, i64 %v84)
  %v86 = trunc i64 %v85 to i16
  %v87 = lshr i64 %v85, 16
  %v88 = trunc i64 %v87 to i16
  %v89 = lshr i64 %v85, 32
  %v90 = trunc i64 %v89 to i16
  %v91 = lshr i64 %v85, 48
  %v92 = trunc i64 %v91 to i16
  %v93 = xor i1 %v15, %v40
  br i1 %v93, label %resultneg, label %resultjoin
resultneg:
  %v94 = sub i16 0, %v86
  %v95 = sub i16 %v94, 0
  %v96 = icmp ne i16 %v86, 0
  %v97 = zext i1 %v96 to i16
  %v98 = or i16 %v97, 0
  %v99 = sub i16 0, %v88
  %v100 = sub i16 %v99, %v98
  %v101 = icmp ne i16 %v88, 0
  %v102 = zext i1 %v101 to i16
  %v103 = or i16 %v102, %v98
  %v104 = sub i16 0, %v90
  %v105 = sub i16 %v104, %v103
  %v106 = icmp ne i16 %v90, 0
  %v107 = zext i1 %v106 to i16
  %v108 = or i16 %v107, %v103
  %v109 = sub i16 0, %v92
  %v110 = sub i16 %v109, %v108
  %v111 = icmp ne i16 %v92, 0
  %v112 = zext i1 %v111 to i16
  %v113 = or i16 %v112, %v108
  br label %resultjoin
resultjoin:
  %v114 = phi i16 [ %v86, %bjoin ], [ %v95, %resultneg ]
  %v115 = phi i16 [ %v88, %bjoin ], [ %v100, %resultneg ]
  %v116 = phi i16 [ %v90, %bjoin ], [ %v105, %resultneg ]
  %v117 = phi i16 [ %v92, %bjoin ], [ %v110, %resultneg ]
  %v118 = zext i16 %v114 to i64
  %v119 = zext i16 %v115 to i64
  %v120 = shl i64 %v119, 16
  %v121 = or i64 %v118, %v120
  %v122 = zext i16 %v116 to i64
  %v123 = shl i64 %v122, 32
  %v124 = or i64 %v121, %v123
  %v125 = zext i16 %v117 to i64
  %v126 = shl i64 %v125, 48
  %v127 = or i64 %v124, %v126
  ret i64 %v127
}

define i64 @__opencpu_srem64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  %v9 = lshr i64 %b, 16
  %v10 = trunc i64 %v9 to i16
  %v11 = lshr i64 %b, 32
  %v12 = trunc i64 %v11 to i16
  %v13 = lshr i64 %b, 48
  %v14 = trunc i64 %v13 to i16
  %v15 = icmp slt i16 %v7, 0
  br i1 %v15, label %aneg, label %ajoin
aneg:
  %v16 = sub i16 0, %v1
  %v17 = sub i16 %v16, 0
  %v18 = icmp ne i16 %v1, 0
  %v19 = zext i1 %v18 to i16
  %v20 = or i16 %v19, 0
  %v21 = sub i16 0, %v3
  %v22 = sub i16 %v21, %v20
  %v23 = icmp ne i16 %v3, 0
  %v24 = zext i1 %v23 to i16
  %v25 = or i16 %v24, %v20
  %v26 = sub i16 0, %v5
  %v27 = sub i16 %v26, %v25
  %v28 = icmp ne i16 %v5, 0
  %v29 = zext i1 %v28 to i16
  %v30 = or i16 %v29, %v25
  %v31 = sub i16 0, %v7
  %v32 = sub i16 %v31, %v30
  %v33 = icmp ne i16 %v7, 0
  %v34 = zext i1 %v33 to i16
  %v35 = or i16 %v34, %v30
  br label %ajoin
ajoin:
  %v36 = phi i16 [ %v1, %entry ], [ %v17, %aneg ]
  %v37 = phi i16 [ %v3, %entry ], [ %v22, %aneg ]
  %v38 = phi i16 [ %v5, %entry ], [ %v27, %aneg ]
  %v39 = phi i16 [ %v7, %entry ], [ %v32, %aneg ]
  %v40 = icmp slt i16 %v14, 0
  br i1 %v40, label %bneg, label %bjoin
bneg:
  %v41 = sub i16 0, %v8
  %v42 = sub i16 %v41, 0
  %v43 = icmp ne i16 %v8, 0
  %v44 = zext i1 %v43 to i16
  %v45 = or i16 %v44, 0
  %v46 = sub i16 0, %v10
  %v47 = sub i16 %v46, %v45
  %v48 = icmp ne i16 %v10, 0
  %v49 = zext i1 %v48 to i16
  %v50 = or i16 %v49, %v45
  %v51 = sub i16 0, %v12
  %v52 = sub i16 %v51, %v50
  %v53 = icmp ne i16 %v12, 0
  %v54 = zext i1 %v53 to i16
  %v55 = or i16 %v54, %v50
  %v56 = sub i16 0, %v14
  %v57 = sub i16 %v56, %v55
  %v58 = icmp ne i16 %v14, 0
  %v59 = zext i1 %v58 to i16
  %v60 = or i16 %v59, %v55
  br label %bjoin
bjoin:
  %v61 = phi i16 [ %v8, %ajoin ], [ %v42, %bneg ]
  %v62 = phi i16 [ %v10, %ajoin ], [ %v47, %bneg ]
  %v63 = phi i16 [ %v12, %ajoin ], [ %v52, %bneg ]
  %v64 = phi i16 [ %v14, %ajoin ], [ %v57, %bneg ]
  %v65 = zext i16 %v36 to i64
  %v66 = zext i16 %v37 to i64
  %v67 = shl i64 %v66, 16
  %v68 = or i64 %v65, %v67
  %v69 = zext i16 %v38 to i64
  %v70 = shl i64 %v69, 32
  %v71 = or i64 %v68, %v70
  %v72 = zext i16 %v39 to i64
  %v73 = shl i64 %v72, 48
  %v74 = or i64 %v71, %v73
  %v75 = zext i16 %v61 to i64
  %v76 = zext i16 %v62 to i64
  %v77 = shl i64 %v76, 16
  %v78 = or i64 %v75, %v77
  %v79 = zext i16 %v63 to i64
  %v80 = shl i64 %v79, 32
  %v81 = or i64 %v78, %v80
  %v82 = zext i16 %v64 to i64
  %v83 = shl i64 %v82, 48
  %v84 = or i64 %v81, %v83
  %v85 = call i64 @__opencpu_urem64(i64 %v74, i64 %v84)
  %v86 = trunc i64 %v85 to i16
  %v87 = lshr i64 %v85, 16
  %v88 = trunc i64 %v87 to i16
  %v89 = lshr i64 %v85, 32
  %v90 = trunc i64 %v89 to i16
  %v91 = lshr i64 %v85, 48
  %v92 = trunc i64 %v91 to i16
  br i1 %v15, label %resultneg, label %resultjoin
resultneg:
  %v93 = sub i16 0, %v86
  %v94 = sub i16 %v93, 0
  %v95 = icmp ne i16 %v86, 0
  %v96 = zext i1 %v95 to i16
  %v97 = or i16 %v96, 0
  %v98 = sub i16 0, %v88
  %v99 = sub i16 %v98, %v97
  %v100 = icmp ne i16 %v88, 0
  %v101 = zext i1 %v100 to i16
  %v102 = or i16 %v101, %v97
  %v103 = sub i16 0, %v90
  %v104 = sub i16 %v103, %v102
  %v105 = icmp ne i16 %v90, 0
  %v106 = zext i1 %v105 to i16
  %v107 = or i16 %v106, %v102
  %v108 = sub i16 0, %v92
  %v109 = sub i16 %v108, %v107
  %v110 = icmp ne i16 %v92, 0
  %v111 = zext i1 %v110 to i16
  %v112 = or i16 %v111, %v107
  br label %resultjoin
resultjoin:
  %v113 = phi i16 [ %v86, %bjoin ], [ %v94, %resultneg ]
  %v114 = phi i16 [ %v88, %bjoin ], [ %v99, %resultneg ]
  %v115 = phi i16 [ %v90, %bjoin ], [ %v104, %resultneg ]
  %v116 = phi i16 [ %v92, %bjoin ], [ %v109, %resultneg ]
  %v117 = zext i16 %v113 to i64
  %v118 = zext i16 %v114 to i64
  %v119 = shl i64 %v118, 16
  %v120 = or i64 %v117, %v119
  %v121 = zext i16 %v115 to i64
  %v122 = shl i64 %v121, 32
  %v123 = or i64 %v120, %v122
  %v124 = zext i16 %v116 to i64
  %v125 = shl i64 %v124, 48
  %v126 = or i64 %v123, %v125
  ret i64 %v126
}

define i64 @__opencpu_mul64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  %v9 = lshr i64 %b, 16
  %v10 = trunc i64 %v9 to i16
  %v11 = lshr i64 %b, 32
  %v12 = trunc i64 %v11 to i16
  %v13 = lshr i64 %b, 48
  %v14 = trunc i64 %v13 to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %a2 = phi i16 [ %v5, %entry ], [ %ax2, %step ]
  %a3 = phi i16 [ %v7, %entry ], [ %ax3, %step ]
  %b0 = phi i16 [ %v8, %entry ], [ %bx0, %step ]
  %b1 = phi i16 [ %v10, %entry ], [ %bx1, %step ]
  %b2 = phi i16 [ %v12, %entry ], [ %bx2, %step ]
  %b3 = phi i16 [ %v14, %entry ], [ %bx3, %step ]
  %r0 = phi i16 [ 0, %entry ], [ %rx0, %step ]
  %r1 = phi i16 [ 0, %entry ], [ %rx1, %step ]
  %r2 = phi i16 [ 0, %entry ], [ %rx2, %step ]
  %r3 = phi i16 [ 0, %entry ], [ %rx3, %step ]
  %count = phi i16 [ 64, %entry ], [ %countx, %step ]
  br label %step
step:
  %v15 = and i16 %b0, 1
  %v16 = sub i16 0, %v15
  %v17 = and i16 %a0, %v16
  %v18 = add i16 %r0, %v17
  %v19 = icmp ult i16 %v18, %r0
  %v20 = add i16 %v18, 0
  %v21 = icmp ult i16 %v20, %v18
  %v22 = or i1 %v19, %v21
  %v23 = zext i1 %v22 to i16
  %v24 = and i16 %a1, %v16
  %v25 = add i16 %r1, %v24
  %v26 = icmp ult i16 %v25, %r1
  %v27 = add i16 %v25, %v23
  %v28 = icmp ult i16 %v27, %v25
  %v29 = or i1 %v26, %v28
  %v30 = zext i1 %v29 to i16
  %v31 = and i16 %a2, %v16
  %v32 = add i16 %r2, %v31
  %v33 = icmp ult i16 %v32, %r2
  %v34 = add i16 %v32, %v30
  %v35 = icmp ult i16 %v34, %v32
  %v36 = or i1 %v33, %v35
  %v37 = zext i1 %v36 to i16
  %v38 = and i16 %a3, %v16
  %v39 = add i16 %r3, %v38
  %v40 = icmp ult i16 %v39, %r3
  %v41 = add i16 %v39, %v37
  %v42 = icmp ult i16 %v41, %v39
  %v43 = or i1 %v40, %v42
  %v44 = zext i1 %v43 to i16
  %v45 = shl i16 %a0, 1
  %v46 = or i16 %v45, 0
  %v47 = shl i16 %a1, 1
  %v48 = lshr i16 %a0, 15
  %v49 = or i16 %v47, %v48
  %v50 = shl i16 %a2, 1
  %v51 = lshr i16 %a1, 15
  %v52 = or i16 %v50, %v51
  %v53 = shl i16 %a3, 1
  %v54 = lshr i16 %a2, 15
  %v55 = or i16 %v53, %v54
  %v56 = lshr i16 %b0, 1
  %v57 = shl i16 %b1, 15
  %v58 = or i16 %v56, %v57
  %v59 = lshr i16 %b1, 1
  %v60 = shl i16 %b2, 15
  %v61 = or i16 %v59, %v60
  %v62 = lshr i16 %b2, 1
  %v63 = shl i16 %b3, 15
  %v64 = or i16 %v62, %v63
  %v65 = lshr i16 %b3, 1
  %v66 = or i16 %v65, 0
  %ax0 = add i16 %v46, 0
  %bx0 = add i16 %v58, 0
  %rx0 = add i16 %v20, 0
  %ax1 = add i16 %v49, 0
  %bx1 = add i16 %v61, 0
  %rx1 = add i16 %v27, 0
  %ax2 = add i16 %v52, 0
  %bx2 = add i16 %v64, 0
  %rx2 = add i16 %v34, 0
  %ax3 = add i16 %v55, 0
  %bx3 = add i16 %v66, 0
  %rx3 = add i16 %v41, 0
  %countx = sub i16 %count, 1
  %v67 = icmp eq i16 %countx, 0
  br i1 %v67, label %exit, label %loop
exit:
  %v68 = zext i16 %v20 to i64
  %v69 = zext i16 %v27 to i64
  %v70 = shl i64 %v69, 16
  %v71 = or i64 %v68, %v70
  %v72 = zext i16 %v34 to i64
  %v73 = shl i64 %v72, 32
  %v74 = or i64 %v71, %v73
  %v75 = zext i16 %v41 to i64
  %v76 = shl i64 %v75, 48
  %v77 = or i64 %v74, %v76
  ret i64 %v77
}

define i64 @__opencpu_shl64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %a2 = phi i16 [ %v5, %entry ], [ %ax2, %step ]
  %a3 = phi i16 [ %v7, %entry ], [ %ax3, %step ]
  %count = phi i16 [ %v8, %entry ], [ %countx, %step ]
  %v9 = icmp eq i16 %count, 0
  br i1 %v9, label %exit, label %step
step:
  %v10 = shl i16 %a0, 1
  %v11 = or i16 %v10, 0
  %v12 = shl i16 %a1, 1
  %v13 = lshr i16 %a0, 15
  %v14 = or i16 %v12, %v13
  %v15 = shl i16 %a2, 1
  %v16 = lshr i16 %a1, 15
  %v17 = or i16 %v15, %v16
  %v18 = shl i16 %a3, 1
  %v19 = lshr i16 %a2, 15
  %v20 = or i16 %v18, %v19
  %ax0 = add i16 %v11, 0
  %ax1 = add i16 %v14, 0
  %ax2 = add i16 %v17, 0
  %ax3 = add i16 %v20, 0
  %countx = sub i16 %count, 1
  br label %loop
exit:
  %v21 = zext i16 %a0 to i64
  %v22 = zext i16 %a1 to i64
  %v23 = shl i64 %v22, 16
  %v24 = or i64 %v21, %v23
  %v25 = zext i16 %a2 to i64
  %v26 = shl i64 %v25, 32
  %v27 = or i64 %v24, %v26
  %v28 = zext i16 %a3 to i64
  %v29 = shl i64 %v28, 48
  %v30 = or i64 %v27, %v29
  ret i64 %v30
}

define i64 @__opencpu_lshr64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %a2 = phi i16 [ %v5, %entry ], [ %ax2, %step ]
  %a3 = phi i16 [ %v7, %entry ], [ %ax3, %step ]
  %count = phi i16 [ %v8, %entry ], [ %countx, %step ]
  %v9 = icmp eq i16 %count, 0
  br i1 %v9, label %exit, label %step
step:
  %v10 = lshr i16 %a0, 1
  %v11 = shl i16 %a1, 15
  %v12 = or i16 %v10, %v11
  %v13 = lshr i16 %a1, 1
  %v14 = shl i16 %a2, 15
  %v15 = or i16 %v13, %v14
  %v16 = lshr i16 %a2, 1
  %v17 = shl i16 %a3, 15
  %v18 = or i16 %v16, %v17
  %v19 = lshr i16 %a3, 1
  %v20 = or i16 %v19, 0
  %ax0 = add i16 %v12, 0
  %ax1 = add i16 %v15, 0
  %ax2 = add i16 %v18, 0
  %ax3 = add i16 %v20, 0
  %countx = sub i16 %count, 1
  br label %loop
exit:
  %v21 = zext i16 %a0 to i64
  %v22 = zext i16 %a1 to i64
  %v23 = shl i64 %v22, 16
  %v24 = or i64 %v21, %v23
  %v25 = zext i16 %a2 to i64
  %v26 = shl i64 %v25, 32
  %v27 = or i64 %v24, %v26
  %v28 = zext i16 %a3 to i64
  %v29 = shl i64 %v28, 48
  %v30 = or i64 %v27, %v29
  ret i64 %v30
}

define i64 @__opencpu_ashr64(i64 %a, i64 %b) #0 {
entry:
  %v1 = trunc i64 %a to i16
  %v2 = lshr i64 %a, 16
  %v3 = trunc i64 %v2 to i16
  %v4 = lshr i64 %a, 32
  %v5 = trunc i64 %v4 to i16
  %v6 = lshr i64 %a, 48
  %v7 = trunc i64 %v6 to i16
  %v8 = trunc i64 %b to i16
  br label %loop
loop:
  %a0 = phi i16 [ %v1, %entry ], [ %ax0, %step ]
  %a1 = phi i16 [ %v3, %entry ], [ %ax1, %step ]
  %a2 = phi i16 [ %v5, %entry ], [ %ax2, %step ]
  %a3 = phi i16 [ %v7, %entry ], [ %ax3, %step ]
  %count = phi i16 [ %v8, %entry ], [ %countx, %step ]
  %v9 = icmp eq i16 %count, 0
  br i1 %v9, label %exit, label %step
step:
  %v10 = lshr i16 %a0, 1
  %v11 = shl i16 %a1, 15
  %v12 = or i16 %v10, %v11
  %v13 = lshr i16 %a1, 1
  %v14 = shl i16 %a2, 15
  %v15 = or i16 %v13, %v14
  %v16 = lshr i16 %a2, 1
  %v17 = shl i16 %a3, 15
  %v18 = or i16 %v16, %v17
  %v19 = lshr i16 %a3, 1
  %v20 = and i16 %a3, -32768
  %v21 = or i16 %v19, %v20
  %ax0 = add i16 %v12, 0
  %ax1 = add i16 %v15, 0
  %ax2 = add i16 %v18, 0
  %ax3 = add i16 %v21, 0
  %countx = sub i16 %count, 1
  br label %loop
exit:
  %v22 = zext i16 %a0 to i64
  %v23 = zext i16 %a1 to i64
  %v24 = shl i64 %v23, 16
  %v25 = or i64 %v22, %v24
  %v26 = zext i16 %a2 to i64
  %v27 = shl i64 %v26, 32
  %v28 = or i64 %v25, %v27
  %v29 = zext i16 %a3 to i64
  %v30 = shl i64 %v29, 48
  %v31 = or i64 %v28, %v30
  ret i64 %v31
}

attributes #0 = { nounwind "opencpu-runtime" }
