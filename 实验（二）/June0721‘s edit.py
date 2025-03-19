import  time
date = time.localtime()      # 获取当前日期时间
print(date)
year, month, day = date[:3]  # 获取年月日
print(year, month, day)
day_month=[ 31,28,31,30,31,30,31,31,30,31,30,31 ]
if year%400==0 or (year % 4==0 and year %100!=0):
    day_month[1]=29
if month==1:
   print(f'今天是今年的第{day}天' )
else:
   print(f'今天是今年的第{sum(day_month[:month-1])+day}天' )
