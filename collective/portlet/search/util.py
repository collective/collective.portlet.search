# -*- coding:utf-8 -*-

import calendar

def getPreviousMonth(year, month):
    if month==0 or month==1:
        month, year = 12, year - 1
    else:
        month-=1
    return (year, month)

def getNextMonth(year, month):
    if month==12:
        month, year = 1, year + 1
    else:
        month+=1
    return (year, month)

def monthcalendar(year,month):
    pYear, pMonth = getPreviousMonth(year,month)
    nYear, nMonth = getNextMonth(year,month)
    
    previous_month = calendar.monthcalendar(pYear, pMonth)
    next_month = calendar.monthcalendar(nYear, nMonth)
    
    this_month = calendar.monthcalendar(year,month)    
    this_month = [[(d and '%d/%02d/%02d' % (year,month,d) or d) for d in w] for w in this_month]
    
    # we know calendar.monthcalendar will 
    # only return previous_month dates in the first week
    first_week = this_month[0]
    # and next_month dates in the last week
    last_week = this_month[-1]
    
    # Add previous_month days
    while 0 in first_week:
        index = first_week.index(0)
        first_week[index] = '%d/%02d/%02d' % (pYear, pMonth, previous_month[-1][index])
    
    # Add next_month days
    while 0 in last_week:
        index = last_week.index(0)
        last_week[index] = '%d/%02d/%02d' % (nYear, nMonth, next_month[0][index])
    
    return this_month


