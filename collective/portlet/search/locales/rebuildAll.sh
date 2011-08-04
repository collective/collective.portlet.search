#!/bin/bash
# kudos to Products.Ploneboard for the base for this file
# ensure that when something is wrong, nothing is broken more than it should...
set -e

# first, create some pot containing anything
i18ndude rebuild-pot --pot collective.portlet.search.pot --create collective.portlet.search --merge manual.pot ..

# finally, update the po files
i18ndude sync --pot collective.portlet.search.pot  `find . -iregex '.*collective.portlet.search\.po$'|grep -v plone`

