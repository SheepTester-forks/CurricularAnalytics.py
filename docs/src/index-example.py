from curricularanalytics import Course, Curriculum, DegreePlan, Term, co, pre, strict_co

bw101 = Course("Introduction to Baskets", 3, prefix="BW", num="101")
bw101l = Course("Introduction to Baskets Lab", 1, prefix="BW", num="101L")
bw111 = Course("Basic Basket Forms", 3, prefix="BW", num="111")
bw201 = Course("Advanced Basketry", 3, prefix="BW", num="201")

bw101l.add_requisite(bw101, strict_co)
bw111.add_requisite(bw101, pre)
bw201.add_requisite(bw111, co)

curriculum = Curriculum("Basket Weaving", [bw101, bw101, bw111, bw201])

terms = [Term([bw101, bw101l]), Term([bw111, bw201])]
degree_plan = DegreePlan("2-Term Plan", curriculum, terms)
