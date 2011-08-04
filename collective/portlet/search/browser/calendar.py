# -*- coding:utf-8 -*-
from time import localtime
from Acquisition import aq_parent, aq_inner
from plone.memoize.compress import xhtml_compress
from Products.CMFPlone.utils import getToolByName
from zope.component import getMultiAdapter, getUtility
from zope.i18nmessageid import MessageFactory
from collective.portlet.search import util
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five import BrowserView

PLMF = MessageFactory('plonelocales')

class CalendarView(BrowserView):
    _template = ViewPageTemplateFile('calendar.pt')
    updated = False
    
    def update(self):
        if self.updated:
            return
        self.updated = True

        context = aq_inner(self.context)
        self.calendar = getToolByName(context, 'portal_calendar')
        self._ts = getToolByName(context, 'translation_service')
        
        self.now = localtime()
        self.yearmonth = yearmonth = self.getYearAndMonthToDisplay()
        self.year = year = yearmonth[0]
        self.month = month = yearmonth[1]

        self.showPrevMonth = yearmonth > (self.now[0]-1, self.now[1])
        self.showNextMonth = yearmonth < (self.now[0]+1, self.now[1])

        self.prevMonthYear, self.prevMonthMonth = self.getPreviousMonth(year, month)
        self.nextMonthYear, self.nextMonthMonth = self.getNextMonth(year, month)

        self.monthName = PLMF(self._ts.month_msgid(month),
                              default=self._ts.month_english(month))
    
    def __call__(self, *args, **kwargs):
        self.update()
        return xhtml_compress(self._template())
    
    def getYearAndMonthToDisplay(self):
        session = None
        request = self.request

        # First priority goes to the data in the REQUEST
        year = request.get('year', None)
        month = request.get('month', None)

        # Next get the data from the SESSION
        if self.calendar.getUseSession():
            session = request.get('SESSION', None)
            if session:
                if not year:
                    year = session.get('calendar_year', None)
                if not month:
                    month = session.get('calendar_month', None)

        # Last resort to today
        if not year:
            year = self.now[0]
        if not month:
            month = self.now[1]

        year, month = int(year), int(month)

        # Store the results in the session for next time
        if session:
            session.set('calendar_year', year)
            session.set('calendar_month', month)

        # Finally return the results
        return year, month
    
    def getPreviousMonth(self, year, month):
        if month==0 or month==1:
            month, year = 12, year - 1
        else:
            month-=1
        return (year, month)
    
    def getNextMonth(self, year, month):
        if month==12:
            month, year = 1, year + 1
        else:
            month+=1
        return (year, month)
    
    def getWeekdays(self):
        """Returns a list of Messages for the weekday names."""
        weekdays = []
        # list of ordered weekdays as numbers
        for day in self.calendar.getDayNumbers():
            weekdays.append(PLMF(self._ts.day_msgid(day, format='s'),
                                 default=self._ts.weekday_english(day, format='a')))

        return weekdays
    
    def isToday(self, day):
        """Returns True if the given day and the current month and year equals
           today, otherwise False.
        """
        return self.now[2]==day and self.now[1]==self.month and \
               self.now[0]==self.year

    def renderCalendar(self):
        """ recreates a sequence of weeks, by days each day is a mapping.
            {'day': #, 'date': '','thisMonth':bool}
        """
        year = int(self.year)
        month = int(self.month)
        daysByWeek = util.monthcalendar(year, month)
        weeks = []

        for week in daysByWeek:
            days = []
            for date in week:
                y,m,d = date.split('/')
                days.append({'day': int(d), 
                             'date': date, 
                             'thisMonth':int(m) == month,
                             'is_today':(self.isToday(int(d)) and int(m) == month)})
            weeks.append(days)
        return weeks