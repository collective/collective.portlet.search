from StringIO import StringIO
from zope.interface import Interface
from zope.interface import implements
from Acquisition import aq_inner

from zope.component import getMultiAdapter

from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from zope import schema
from zope.formlib import form
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.memoize import ram
from plone.memoize.compress import xhtml_compress


from Products.ATContentTypes.interface import IATTopic
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.portlet.search import util
from plone.app.portlets import cache
from plone.app.portlets.portlets.calendar import Renderer as BaseRenderer
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget

from collective.portlet.search import MessageFactory as _

from zope.i18nmessageid import MessageFactory

def _render_calendar_cachekey(fun, self):
    # Create a cachekey for calendar template
    context = aq_inner(self.context)
    if not self.updated:
        self.update()
    
    if self.calendar.getUseSession():
        raise ram.DontCache()
    else:
        key = StringIO()
        print >> key, 'AdvancedSearch'
        print >> key, self.navigation_root_url
        print >> key, cache.get_language(context, self.request)
        print >> key, self.calendar.getFirstWeekDay()
        year, month = self.getYearAndMonthToDisplay()
        print >> key, year
        print >> key, month
                
        return key.getvalue()

def _render_portlet_cachekey(fun, self):
    # Create a cachekey for calendar template
    context = aq_inner(self.context)
    if not self.updated:
        self.update()
    key = StringIO()
    year, month = self.getYearAndMonthToDisplay()
    print >> key, 'AdvancedSearch'
    print >> key, self.title
    print >> key, self.navigation_root_url
    print >> key, cache.get_language(context, self.request)
    print >> key, self.root
    print >> key, self.use_calendar
    print >> key, self.use_daterange
    print >> key, self.use_portal_types
    print >> key, self.use_keyword    
    print >> key, year
    print >> key, month
            
    return key.getvalue()

class IAdvancedSearch(IPortletDataProvider):
    """
    """
    title = schema.TextLine(title=_(u"Title"),
                            description=_(u"Portlet title"),
                            default=_(u"Search"),
                            required=True)
                            
    root = schema.Choice(
            title=_(u"label_advsearch_root_path", default=u"Root node"),
            description=_(u'help_advsearch_root',
                          default=u"You may search for and choose a folder "
                                    "to act as the root of search for this "
                                    "portlet. "
                                    "Leave blank to use the Plone site root. "),
            required=False,
            source=SearchableTextSourceBinder({'is_folderish': True},
                                              default_query='path:'))
                                              
    use_calendar = schema.Bool(title = _(u"Use calendar"),
                               description = _(u"Use a calendar to restrict search to a given date."),
                               default = False,
                               required = False)
    
    use_daterange = schema.Bool(title = _(u"Use date range"),
                                description = _(u"Use fields to restrict search to an interval of time."),
                                default = False,
                                required = False)

    use_keyword = schema.Bool(title = _(u"Use keyword search"),
                                description = _(u"Search using keywords."),
                                default = False,
                                required = False)

    use_portal_types = schema.Bool(title = _(u"Use portal types selection"),
                                description = _(u"Allow user to select wich portal types will be shown."),
                                default = False,
                                required = False)

class Assignment(base.Assignment):
    """Portlet assignment.
    """

    implements(IAdvancedSearch)
    root = None
    title = u''
    use_calendar = False
    use_daterange = False
    use_keyword = False
    use_portal_types = False
    
    def __init__(self,title,
                 root=None,
                 use_calendar=False,
                 use_daterange=False,
                 use_keyword=False,
                 use_portal_types=False,
                  ):
        self.root = root
        self.title = title
        self.use_calendar = use_calendar
        self.use_daterange = use_daterange
        self.use_keyword = use_keyword
        self.use_portal_types = use_portal_types        

class Renderer(BaseRenderer):
    """Portlet renderer.
    """
    
    _template = ViewPageTemplateFile('advancedsearch.pt')
    _templatecalendar = ViewPageTemplateFile('calendar.pt')
        
    def __init__(self, context, request, view, manager, data):
        BaseRenderer.__init__(self, context, request, view, manager, data)
        portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
        portal_tools = getMultiAdapter((context, request), name=u'plone_tools')
        self.navigation_root_url = portal_state.navigation_root_url()
        self.portal_types = portal_tools.types()
        self.friendly_types = portal_state.friendly_types()
    
    @ram.cache(_render_portlet_cachekey)
    def render(self):
        return xhtml_compress(self._template())
    
    def search_form(self):
        return '%s/search_form' % self.navigation_root_url

    def search_action(self):
        return '%s/search' % self.navigation_root_url
    
    def hasTitle(self):
        ''' Show title only if user informed a title in the Assignment form
        '''
        title = self.title
        title.strip()
        return title and True or False
    
    @property
    def title(self):
        return self.data.title
    
    @property
    def root(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                        name=u'plone_portal_state')
        if self.data.root:
            navigation_root_path = '%s%s' % (portal_state.navigation_root_path(), self.data.root)
        else:
            navigation_root_path = portal_state.navigation_root_path()
        return navigation_root_path
    
    @property
    def use_calendar(self):
        return self.data.use_calendar
    
    @property
    def use_daterange(self):
        return self.data.use_daterange
    
    @property
    def use_keyword(self):
        return self.data.use_keyword
    
    @property
    def use_portal_types(self):
        return self.data.use_portal_types
    
    @property
    def used_types(self):
        return self.friendly_types
    
    @ram.cache(_render_calendar_cachekey)
    def renderedCalendar(self):
        ''' Cache the calendar page template'''
        return self._templatecalendar()
    
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
                             'is_today':self.isToday(int(d))})
            weeks.append(days)
        return weeks
    
class AddForm(base.AddForm):
    """Portlet add form.
    """
    form_fields = form.Fields(IAdvancedSearch)
    form_fields['root'].custom_widget = UberSelectionWidget
    
    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.
    """
    form_fields = form.Fields(IAdvancedSearch)
    form_fields['root'].custom_widget = UberSelectionWidget
