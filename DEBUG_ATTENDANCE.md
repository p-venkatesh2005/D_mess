# 🔍 Debug Attendance Not Showing

## Issue
After scanning QR for breakfast, the attendance chart doesn't show any records.

---

## 🧪 **Quick Checks to Run**

### **1. Check if QRScan Records Exist in Database**

Run this SQL in Neon:

```sql
-- Check if QRScan table exists and has data
SELECT * FROM qr_scans 
ORDER BY scan_time DESC 
LIMIT 10;

-- Count total scans
SELECT COUNT(*) as total_scans FROM qr_scans;

-- Count scans by meal
SELECT meal_session, COUNT(*) as count 
FROM qr_scans 
GROUP BY meal_session;

-- Check today's scans
SELECT 
    qs.id,
    qs.scan_date,
    qs.meal_session,
    qs.scan_time,
    u.name as student_name,
    u.phone
FROM qr_scans qs
JOIN students s ON qs.student_id = s.id
JOIN users u ON s.user_id = u.id
WHERE qs.scan_date = CURRENT_DATE
ORDER BY qs.scan_time DESC;
```

---

### **2. Check if Scan Was Actually Created**

After scanning QR as student:

```sql
-- Replace phone number with actual student phone
SELECT 
    qs.*,
    u.name,
    u.phone
FROM qr_scans qs
JOIN students s ON qs.student_id = s.id
JOIN users u ON s.user_id = u.id
WHERE u.phone = '8111111111'  -- Your test student phone
ORDER BY qs.scan_time DESC;
```

---

### **3. Check Current Time and Meal Detection**

```sql
-- Check current time (should be IST aware)
SELECT CURRENT_TIMESTAMP, CURRENT_DATE;

-- What meal should be active based on current hour?
-- Breakfast: 5-11 AM IST
-- Lunch: 11 AM-4 PM IST
-- Dinner: 4-11 PM IST
```

---

## 🐛 **Possible Issues:**

### **Issue 1: QRScan Table Doesn't Exist**

**Symptom:** SQL query fails with "relation 'qr_scans' does not exist"

**Solution:**
```python
# Run in Render Shell or locally
python << 'EOF'
from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ All tables created")
EOF
```

---

### **Issue 2: Time Zone Issues**

**Symptom:** Meal detection returns `None` because IST time calculation is wrong

**Check in Python:**
```python
python << 'EOF'
from datetime import datetime
import pytz

# Check IST time
tz = pytz.timezone('Asia/Kolkata')
ist_now = datetime.now(tz)
hour = ist_now.hour

print(f"IST Time: {ist_now}")
print(f"Hour: {hour}")

# Which meal?
if 5 <= hour < 11:
    print("Meal: Breakfast")
elif 11 <= hour < 16:
    print("Meal: Lunch")
elif 16 <= hour < 23:
    print("Meal: Dinner")
else:
    print("Meal: NONE (outside hours)")
EOF
```

---

### **Issue 3: Student ID Mismatch**

**Symptom:** Scan is created but with wrong student_id

**Check:**
```sql
-- Verify student exists and has correct ID
SELECT 
    u.id as user_id,
    u.name,
    u.phone,
    s.id as student_id
FROM users u
LEFT JOIN students s ON u.id = s.user_id
WHERE u.phone = '8111111111';
```

---

### **Issue 4: Subscription Blocking Scan**

**Symptom:** Scan is rejected because subscription appears inactive

**Check:**
```sql
SELECT 
    u.name,
    u.phone,
    s.subscription_status,
    s.subscription_start,
    s.subscription_end,
    s.subscription_end >= CURRENT_DATE as is_valid
FROM students s
JOIN users u ON s.user_id = u.id
WHERE u.phone = '8111111111';
```

If `subscription_end` is NULL or in the past, the scan will be blocked!

**Fix:**
```sql
-- Set valid subscription dates
UPDATE students s
SET 
    subscription_status = 'active',
    subscription_start = CURRENT_DATE,
    subscription_end = CURRENT_DATE + INTERVAL '30 days'
FROM users u
WHERE s.user_id = u.id AND u.phone = '8111111111';
```

---

### **Issue 5: Flash Messages Not Visible**

**Symptom:** Scan fails but error message not shown

**Check Render logs:**
```
Look for:
- "Invalid QR code"
- "QR code has expired"
- "No meal session is active"
- "Subscription expired" or access denied messages
```

---

## 🔧 **Manual Test Flow**

### **1. As Student (Login and Check)**

```
1. Login as student
2. Go to dashboard
3. Check subscription status - must be ACTIVE
4. Note the current time (IST)
5. Click "Scan QR Now"
6. Point at admin's QR code
7. Should redirect to confirmation page
```

### **2. Check Confirmation Page**

After scanning, you should see:
```
✅ Attendance Marked!
Meal: Breakfast
Time: 10:30 AM IST
Date: 20 Jun 2026
```

If you see error instead:
- ❌ "Invalid QR code" → Token mismatch
- ❌ "QR expired" → Date mismatch
- ❌ "No meal session active" → Time is outside meal hours
- ❌ "Subscription expired" → Fix subscription first

---

## 📊 **Check Chart Data Query**

The attendance chart uses this query:

```python
# In admin.py attendance_chart()
for d in date_range:
    for meal in ['breakfast', 'lunch', 'dinner']:
        counts[meal] = QRScan.query.filter_by(
            scan_date=d, 
            meal_session=meal
        ).count()
```

**Test in SQL:**
```sql
-- Same query in SQL
SELECT 
    scan_date,
    meal_session,
    COUNT(*) as scan_count
FROM qr_scans
WHERE scan_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY scan_date, meal_session
ORDER BY scan_date DESC, meal_session;
```

If this returns 0 rows, no scans exist in database!

---

## 🆘 **Quick Debug: Add Logging**

Temporarily add debug logging to see what's happening:

```python
# In student.py qr_scan() route, add after successful scan:
print(f"✅ QRScan created: student_id={student.id}, date={today}, meal={meal}")

# Check Render logs after scanning
```

---

## ✅ **Most Likely Issues:**

1. **Subscription dates not set** → Run SQL fix from earlier
2. **Time zone issue** → Meal detection returning None
3. **QRScan table missing** → Run db.create_all()
4. **Student ID mismatch** → Check student exists in database

**Run the SQL checks above and share the results!**
