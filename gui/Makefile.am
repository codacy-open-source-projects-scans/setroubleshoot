ICON_FILES = \
	scalable/setroubleshoot_red_icon.svg \
	scalable/setroubleshoot_icon.svg \
	scalable/setroubleshoot_icon-symbolic.svg 

GUI_FILES =              \
	browser.glade           \
	bug_report.glade        \
	fail_dialog.glade    \
	success_dialog.glade \
	style.css		\
	$(NULL)

icondir = $(datadir)/icons/hicolor/

pkggui_DATA = $(GUI_FILES)

EXTRA_DIST =			\
	$(GUI_FILES)		\
	$(ICON_FILES)		\
	$(NULL)

install-data-hook:
	for i in $(ICON_FILES); do d=`dirname $$i`; \
		$(mkdir_p)  $(DESTDIR)$(icondir)$$d/apps;\
		install --mode 644 $$i $(DESTDIR)$(icondir)$$d/apps; done
	$(mkdir_p)  $(DESTDIR)$(datadir)/setroubleshoot/gui
	$(LN_S) -f $(icondir)scalable/apps/setroubleshoot_icon.svg $(DESTDIR)$(datadir)/setroubleshoot/gui
