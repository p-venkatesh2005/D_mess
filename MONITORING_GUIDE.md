# 📊 MONITORING GUIDE - DWARAKA MESS

## 🎯 ONGOING MONITORING & MAINTENANCE

**How to keep your app healthy and running smoothly**

---

## 📅 DAILY MONITORING (2 minutes/day)

### **What to Check:**
1. **App is accessible**
   - Visit: `https://your-app.onrender.com`
   - Should load within 60 seconds (may take 30-60s if sleeping)
   - Login should work

2. **Recent activity**
   - Admin → Dashboard
   - Check today's stats:
     - QR scans today
     - Pending payments
     - Active subscriptions

### **Red Flags:**
- ❌ App won't load after 2 minutes
- ❌ Login fails
- ❌ Database connection errors
- ❌ No QR scans when students are present

### **Action if issues:**
- Check Render dashboard for deployment errors
- Check Render logs for error messages
- Verify environment variables are set

---

## 📅 WEEKLY MONITORING (5 minutes/week)

### **What to Check:**

#### **1. Render Dashboard**
Visit: https://dashboard.render.com/

- [ ] Latest deploy status: "Deploy live" ✅
- [ ] No failed deploys this week
- [ ] Hours used: <180 hours/week (should be ~168)
- [ ] No error spikes in logs

#### **2. Cloudinary Dashboard**
Visit: https://console.cloudinary.com/

- [ ] Storage used: <25 GB (should be <2 GB for <500 students)
- [ ] Bandwidth used: <6 GB/week
- [ ] New uploads appearing correctly

#### **3. Application Health**
- [ ] Login works for admin and students
- [ ] Payment uploads work
- [ ] QR attendance works
- [ ] No student complaints

### **Red Flags:**
- ❌ Cloudinary storage >20 GB (approaching limit)
- ❌ Render hours >700/month
- ❌ Multiple payment upload failures
- ❌ QR scans not recording

### **Action if issues:**
- Review Cloudinary media library for duplicates/corrupted files
- Check for orphaned images
- Run cleanup if approaching limits

---

## 📅 MONTHLY MONITORING (15 minutes/month)

### **What to Check:**

#### **1. Storage Report (CRITICAL)**
Visit: `/admin/storage-report`

**Check:**
- [ ] PostgreSQL usage: <100 MB (20% of 500 MB limit)
- [ ] Cloudinary status: ✅ Enabled
- [ ] Payment storage breakdown
- [ ] Cleanup candidates count

**Action:**
```
IF PostgreSQL >200 MB:
  → Run "Full Cleanup" immediately
  
IF Cloudinary >15 GB:
  → Check for orphaned images
  → Run cleanup
  
IF many cleanup candidates (>10,000):
  → Run cleanup (normal for monthly cleanup)
```

#### **2. Neon Database Health**
Visit: https://console.neon.tech/

**Check:**
- [ ] Storage: <0.3 GB (60% of 0.5 GB limit)
- [ ] Active connections: <10
- [ ] No slow queries
- [ ] Backups enabled

**Queries to run in SQL Editor:**
```sql
-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC
LIMIT 10;

-- Check row counts
SELECT 
    'qr_scans' as table, COUNT(*) as rows FROM qr_scans
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'students', COUNT(*) FROM students
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
ORDER BY rows DESC;
```

#### **3. Run Monthly Cleanup**
Visit: `/admin/storage-report`

**Steps:**
1. Review "Cleanup Candidates" section
2. Note counts:
   - Old QR scans (>12 months): _______
   - Old attendance (>12 months): _______
   - Old orders (>6 months): _______
   - Rejected payments (>30 days): _______
3. Click "Run Full Cleanup" button
4. Verify success message
5. Check storage decreased

**Expected Results:**
- QR scans deleted: 5,000-50,000 (depending on usage)
- Attendance deleted: 1,000-10,000
- Storage reduction: 10-50 MB

#### **4. Verify Subscriptions**
Admin → Students → Filter: Active

**Check:**
- [ ] All active subscriptions have valid end dates
- [ ] No expired subscriptions showing as "active"
- [ ] Subscription dates match payment upload dates

**SQL Query to check:**
```sql
-- Find active subscriptions that should be expired
SELECT 
    s.id, 
    u.name, 
    s.subscription_status,
    s.subscription_end
FROM students s
JOIN users u ON s.user_id = u.id
WHERE s.subscription_status = 'active'
AND s.subscription_end < CURRENT_DATE;
```

Should return **0 rows** ✅

#### **5. Payment Verification Backlog**
Admin → Payments → Filter: Pending

**Check:**
- [ ] Pending payments <10 (should be verified quickly)
- [ ] No payments pending >7 days
- [ ] All screenshots visible (Cloudinary URLs working)

**Action if backlog:**
- Verify pending payments
- Check if any payment uploads failed
- Remind admin to verify regularly

---

## 📅 QUARTERLY MONITORING (30 minutes/quarter)

### **What to Check:**

#### **1. Free Tier Limits Review**

**Render:**
- Monthly hours: ______ / 750 hours
- Deploys this quarter: ______
- Average response time: ______

**Neon:**
- Storage: ______ GB / 0.5 GB (______%)
- Queries per day: ______
- Growth rate: ______ MB/month

**Cloudinary:**
- Storage: ______ GB / 25 GB (______%)
- Bandwidth per month: ______ GB
- Uploads per month: ______

**Projection:**
```
At current growth rate:
- Neon will hit 80% in: ______ months
- Cloudinary will hit 80% in: ______ months
- Need upgrades in: ______ months
```

#### **2. Performance Review**

**Page Load Times:**
- Login page: ______ seconds
- Student dashboard: ______ seconds
- Admin dashboard: ______ seconds
- Payment upload: ______ seconds
- Attendance chart: ______ seconds

**Targets:**
- All pages <3 seconds ✅
- Payment upload <5 seconds ✅
- Attendance chart <5 seconds ✅

#### **3. Data Quality Audit**

**Check for anomalies:**
```sql
-- Students with no subscriptions
SELECT COUNT(*) FROM students WHERE subscription_status = 'inactive';

-- Payments with no Cloudinary URL (should migrate)
SELECT COUNT(*) FROM payments 
WHERE screenshot_path IS NOT NULL 
AND cloudinary_url IS NULL;

-- QR scans without matching attendance
SELECT COUNT(*) FROM qr_scans 
WHERE scan_date < CURRENT_DATE - INTERVAL '7 days';

-- Orphaned records
SELECT COUNT(*) FROM subscriptions WHERE student_id NOT IN (SELECT id FROM students);
```

#### **4. Security Review**

**Check:**
- [ ] Admin password is strong (>12 characters)
- [ ] No SQL injection vulnerabilities reported
- [ ] HTTPS enabled (🔒 icon in browser)
- [ ] Environment variables not exposed
- [ ] No sensitive data in logs

**Verify in Render logs:**
```
✅ No password leaks
✅ No Cloudinary API secret exposed
✅ No database credentials visible
```

#### **5. User Feedback Collection**

**Ask students/admin:**
- Is the app fast enough?
- Any features missing?
- Any bugs encountered?
- Is payment verification smooth?
- Is QR scanning reliable?

**Document feedback:** _______________________________

---

## 📅 YEARLY MONITORING (1 hour/year)

### **What to Review:**

#### **1. Full Application Audit**

**Usage Statistics (past 12 months):**
- Total students: ______
- Total payments: ______
- Total QR scans: ______
- Total orders: ______
- Average daily active users: ______

**Storage Growth:**
- Neon: Started ______ GB → Now ______ GB
- Cloudinary: Started ______ GB → Now ______ GB
- Growth rate: ______ GB/year

**Projection:**
- Years until Neon upgrade needed: ______
- Years until Cloudinary upgrade needed: ______
- Estimated future costs: $______/year

#### **2. Cleanup Policy Review**

**Current policies:**
- QR scans retention: 12 months
- Attendance retention: 12 months
- Old subscriptions: 24 months
- Feedback: 12 months

**Should we adjust?**
- [ ] Keep as is
- [ ] Increase retention (if storage allows)
- [ ] Decrease retention (if approaching limits)

#### **3. Feature Usage Analysis**

**Which features are used most:**
- [ ] Payment upload: ______ times/month
- [ ] QR attendance: ______ scans/month
- [ ] Menu viewing: ______ views/month
- [ ] Leave requests: ______ requests/month
- [ ] Feedback: ______ submissions/month

**Which features are unused:**
- [ ] _______________________________
- [ ] _______________________________

**Consider:**
- Remove unused features to simplify
- Improve popular features
- Add requested features

#### **4. Technology Stack Update**

**Check for updates:**
- [ ] Flask version: Current ______ Latest ______
- [ ] PostgreSQL: Current ______ Latest ______
- [ ] Python: Current 3.11.9 Latest ______
- [ ] Cloudinary SDK: Current ______ Latest ______

**Security patches:**
- [ ] Check for critical security updates
- [ ] Update dependencies if needed
- [ ] Test after updates

---

## 🚨 EMERGENCY MONITORING

### **When to Check Immediately:**

#### **Scenario 1: App Down**
**Symptoms:**
- App won't load
- 502 Bad Gateway error
- Render shows "Deploy failed"

**Action:**
1. Check Render logs for errors
2. Check recent code changes
3. Rollback if needed: `git revert HEAD`
4. Redeploy from Render dashboard

#### **Scenario 2: Database Connection Lost**
**Symptoms:**
- "Database connection failed" errors
- Students can't login
- Data not saving

**Action:**
1. Check Neon dashboard for outages
2. Verify `DATABASE_URL` environment variable
3. Check Neon connection limit
4. Restart Render service if needed

#### **Scenario 3: Cloudinary Upload Failures**
**Symptoms:**
- Payment uploads fail
- "Cloudinary upload failed" errors
- Screenshots not appearing

**Action:**
1. Check Cloudinary dashboard for issues
2. Verify Cloudinary credentials in Render
3. Check Cloudinary storage not exceeded
4. Test with small file

#### **Scenario 4: Storage Limit Reached**
**Symptoms:**
- "Database is full" errors
- New payments rejected
- App slow or unresponsive

**Action:**
1. Run emergency cleanup immediately
2. Check storage report
3. Delete old QR scans manually if needed:
```sql
DELETE FROM qr_scans 
WHERE scan_date < CURRENT_DATE - INTERVAL '6 months';
```
4. Consider upgrade if repeated

---

## 📊 MONITORING DASHBOARD

### **Create a Spreadsheet to Track:**

```
Date | Neon MB | Cloudinary GB | Students | QR Scans | Payments | Issues
-----|---------|---------------|----------|----------|----------|--------
Jan  |   45    |     1.2       |   120    |  10,500  |    120   |  None
Feb  |   52    |     1.4       |   135    |  12,000  |    135   |  None
Mar  |   48    |     1.5       |   138    |  11,800  |    138   |  None
...
```

**Track monthly to:**
- Identify growth trends
- Predict when upgrades needed
- Spot anomalies early
- Plan capacity

---

## ✅ MONITORING CHECKLIST SUMMARY

### **Daily (2 min):**
- [ ] App loads correctly
- [ ] No major errors

### **Weekly (5 min):**
- [ ] Render status good
- [ ] Cloudinary working
- [ ] No user complaints

### **Monthly (15 min):**
- [ ] Check storage report
- [ ] Run cleanup
- [ ] Verify subscriptions
- [ ] Check payment backlog

### **Quarterly (30 min):**
- [ ] Review free tier limits
- [ ] Performance audit
- [ ] Data quality check
- [ ] Security review

### **Yearly (1 hour):**
- [ ] Full application audit
- [ ] Update technology stack
- [ ] Review cleanup policies
- [ ] Plan for growth

---

## 🎯 SUCCESS METRICS

**Your app is healthy when:**

✅ Neon storage <300 MB (60% of limit)  
✅ Cloudinary storage <15 GB (60% of limit)  
✅ App loads in <60 seconds (including spin-up)  
✅ No payment upload failures  
✅ QR attendance works reliably  
✅ <10 pending payments at any time  
✅ Monthly cleanup runs successfully  
✅ No student complaints  

**If all metrics green → You're doing great! 🎉**

---

## 📞 ESCALATION CONTACTS

**When to escalate:**
- Storage >90% of limit
- Multiple days of downtime
- Data loss or corruption
- Security breach suspected
- Free tier limits consistently exceeded

**Escalation path:**
1. Check documentation first
2. Review logs and error messages
3. Test in isolation
4. If unresolved, consider paid support or community help

---

**Remember:** Proactive monitoring prevents problems!  
**Set reminders:** Monthly cleanup is most important!  
**Track trends:** Storage growth helps plan ahead!

🚀 **Happy monitoring!**
