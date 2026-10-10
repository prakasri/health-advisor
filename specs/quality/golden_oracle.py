"""EV-001 golden-case oracle. Independent of app code: hand-written from CLS-001 text and
monitoring-rules.yaml. Regenerate: python3 specs/quality/golden_oracle.py > specs/quality/golden-cases.jsonl
"""
import json
from decimal import Decimal, ROUND_HALF_UP
def r(x, q="0.1"): return float(Decimal(str(x)).quantize(Decimal(q), rounding=ROUND_HALF_UP))
B = dict(hba1c=6.0, age=40, gender="male", pregnant=False, type1_diabetes=False, comorbidities=["none"],
         family_history=False, height_cm=170, weight_kg=70, activity="sedentary", smoking="never",
         alcohol="none", diet="non_vegetarian", region="western")
cases = [
 ("G01","Ravi — prediabetes, family history, Asian BMI", dict(hba1c=6.1,age=45,family_history=True,height_cm=172,weight_kg=80,alcohol="occasional",region="indian")),
 ("G02","Meena — diabetes range, hypertension, vegetarian", dict(hba1c=7.8,age=58,gender="female",comorbidities=["hypertension"],height_cm=155,weight_kg=68,diet="vegetarian",region="indian")),
 ("G03","Alex — normal, smoker, very active", dict(hba1c=5.3,age=30,height_cm=178,weight_kg=72,activity="very_active",smoking="current",alcohol="occasional")),
 ("G04","Priya — pregnant → referral", dict(hba1c=6.0,age=29,gender="female",pregnant=True,height_cm=160,weight_kg=60,diet="vegetarian",region="indian")),
 ("G05","Joseph — urgent, kidney disease + obesity", dict(hba1c=11.2,age=62,comorbidities=["kidney_disease","obesity"],family_history=True,height_cm=170,weight_kg=98,smoking="former")),
 ("G06","Boundary 5.6 → normal, vegan", dict(hba1c=5.6,age=40,gender="female",height_cm=165,weight_kg=60,activity="moderately_active",diet="vegan",region="mediterranean")),
 ("G07","Boundary 5.7 → prediabetes, dyslipidemia, regular alcohol", dict(hba1c=5.7,age=50,comorbidities=["dyslipidemia"],height_cm=175,weight_kg=85,activity="lightly_active",alcohol="regular")),
 ("G08","Boundary 6.4 → prediabetes, fatty liver, vegetarian", dict(hba1c=6.4,age=38,gender="female",comorbidities=["fatty_liver"],height_cm=160,weight_kg=75,alcohol="occasional",diet="vegetarian",region="indian")),
 ("G09","Boundary 6.5 → diabetes, gender other, vegan", dict(hba1c=6.5,age=55,gender="other",height_cm=170,weight_kg=70,activity="moderately_active",diet="vegan",region="east_asian")),
 ("G10","9.9 → diabetes not urgent, CVD + hypertension, smoker", dict(hba1c=9.9,age=47,comorbidities=["cardiovascular_disease","hypertension"],height_cm=180,weight_kg=95,activity="lightly_active",smoking="current",alcohol="regular",region="indian")),
 ("G11","10.0 → urgent, thyroid, vegetarian", dict(hba1c=10.0,age=66,gender="female",comorbidities=["thyroid_disorder"],height_cm=158,weight_kg=55,diet="vegetarian")),
 ("G12","Age 17 → referral under_18", dict(hba1c=6.8,age=17)),
 ("G13","Type 1 → referral", dict(hba1c=7.5,age=25,type1_diabetes=True)),
 ("G14","Age 17 + pregnant → under_18 wins", dict(hba1c=5.9,age=17,gender="female",pregnant=True)),
 ("G15","Prediabetes, sleep apnoea + obesity", dict(hba1c=6.2,age=52,comorbidities=["sleep_apnoea","obesity"],height_cm=176,weight_kg=110,smoking="former",alcohol="regular",region="mediterranean")),
 ("G16","Normal, underweight, vegetarian", dict(hba1c=5.4,age=24,gender="female",height_cm=165,weight_kg=48,activity="lightly_active",diet="vegetarian",region="indian")),
 ("G17","6.45 rounds to 6.5 → diabetes, family history", dict(hba1c=6.45,age=44,family_history=True,height_cm=170,weight_kg=68,activity="moderately_active",region="east_asian")),
 ("G18","5.65 rounds to 5.7 → prediabetes, hypertension + dyslipidemia", dict(hba1c=5.65,age=60,gender="female",comorbidities=["hypertension","dyslipidemia"],height_cm=162,weight_kg=70,activity="lightly_active")),
 ("G19","Kidney disease, vegan, diabetes range", dict(hba1c=8.4,age=70,comorbidities=["kidney_disease"],height_cm=168,weight_kg=62,diet="vegan",region="indian")),
 ("G20","All eight comorbidities, smoker", dict(hba1c=7.0,age=49,gender="female",comorbidities=["hypertension","dyslipidemia","obesity","cardiovascular_disease","kidney_disease","thyroid_disorder","fatty_liver","sleep_apnoea"],height_cm=160,weight_kg=90,smoking="current",alcohol="occasional",region="indian")),
]
CONST={"male":5,"female":-161,"other":-78}; ACT={"sedentary":1.2,"lightly_active":1.375,"moderately_active":1.55,"very_active":1.725}
FLOOR={"female":1200,"male":1500,"other":1350}
CHECKS={"kidney_disease":"no_high_protein","fatty_liver":"no_alcohol_encouraged"}
out=[]
for cid,desc,over in cases:
    i={**B,**over}; h=r(i["hba1c"]); e={}
    reason = "under_18" if i["age"]<18 else "pregnant" if i["pregnant"] else "type1" if i["type1_diabetes"] else None
    e["eligible"]=reason is None; e["exit_reason"]=reason
    if reason is None:
        cls="normal" if h<5.7 else "prediabetes" if h<6.5 else "diabetes"
        bmi=r(i["weight_kg"]/(i["height_cm"]/100)**2)
        asian=i["region"] in ("indian","east_asian"); ow,ob=(23.0,25.0) if asian else (25.0,30.0)
        cat="underweight" if bmi<18.5 else "normal" if bmi<ow else "overweight" if bmi<ob else "obese"
        bmr=10*i["weight_kg"]+6.25*i["height_cm"]-5*i["age"]+CONST[i["gender"]]
        kcal=bmr*ACT[i["activity"]]-(500 if cat in("overweight","obese") else 0)
        kcal=max(kcal,FLOOR[i["gender"]]); kcal=int(r(kcal/50,"1")*50)
        com=[c for c in i["comorbidities"] if c!="none"]
        rf=[]
        if cls=="prediabetes": rf.append("hba1c_prediabetes")
        if cls=="diabetes": rf.append("hba1c_diabetes")
        if cat=="overweight": rf.append("overweight")
        if cat=="obese": rf.append("obesity")
        if i["family_history"]: rf.append("family_history")
        if i["activity"]=="sedentary": rf.append("inactivity")
        if i["smoking"]=="current": rf.append("smoking")
        if i["alcohol"]=="regular": rf.append("alcohol")
        if i["age"]>=45: rf.append("age_45_plus")
        rf += [f"comorbidity:{c}" for c in com]
        urgent=h>=10.0
        # monitoring: hand-transcribed applies_when from monitoring-rules.yaml
        m=[]
        D=cls=="diabetes"; P=cls=="prediabetes"; N=cls=="normal"; C=set(com)
        if D: m.append("hba1c_diabetes")
        if P: m.append("hba1c_prediabetes")
        if N: m.append("hba1c_screening")
        if P or D: m.append("fasting_glucose")
        if D: m.append("postprandial_glucose")
        if D or C&{"dyslipidemia","cardiovascular_disease"}: m.append("lipid_profile")
        if D or C&{"hypertension","kidney_disease"}: m.append("kidney_function")
        if "fatty_liver" in C or ("obesity" in C and (P or D)): m.append("liver_function")
        if D: m.append("vitamin_b12")
        if C&{"obesity","kidney_disease"}: m.append("vitamin_d")
        if "thyroid_disorder" in C: m.append("thyroid_function")
        if D: m+= ["eye_exam","foot_exam"]
        m.append("blood_pressure")
        if D or "cardiovascular_disease" in C: m.append("cardiovascular_assessment")
        e.update(hba1c_rounded=h,classification=cls,urgent=urgent,bmi=bmi,bmi_category=cat,calorie_target=kcal,
                 risk_factor_ids=rf,monitoring_ids=sorted(m),
                 constraint_checks=sorted({CHECKS[c] for c in com if c in CHECKS}),
                 required_doctor_question_count=len(com))
    out.append({"id":cid,"description":desc,"input":i,"expected":e})
for o in out: print(json.dumps(o))
