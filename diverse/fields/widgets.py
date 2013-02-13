from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.conf import settings
from django import forms

class DiverseFileInput(forms.widgets.FileInput):
    """A AdminFileWidget that shows a delete and update checkbox"""
    input_type = 'file'

    def __init__(self, show_delete_checkbox=True,
                       show_update_checkbox=True, attrs={}):
        super(DiverseFileInput, self).__init__(attrs)
        self.show_delete_checkbox = show_delete_checkbox
        self.show_update_checkbox = show_update_checkbox

    def get_html_tpls(self, input, name, value, attrs):
        return {
            'link':     u'%s&nbsp;<a target="_blank" href="%s%s">%s</a>',
            'field':    u'<br>%s&nbsp;%s',
            'delete':   u' <nobr><input type="checkbox" name="%s_delete" id="id_%s_delete"/> &mdash;' \
                        u' <label style="display: inline; float: none;" for="id_%s_delete">%s</label></nobr>',
            'update':   u' <nobr><input type="checkbox" name="%s_update" id="id_%s_update"/> &mdash;' \
                        u' <label style="display: inline; float: none;" for="id_%s_update">%s</label></nobr>',
        }

    def get_html_tags(self, html_tpls, input, name, value, attrs):
        delete_tag, update_tag = (u'',)*2

        # generate checkboxes
        if self.show_delete_checkbox:
            delete_tag = html_tpls['delete'] % (name, name, name, _('Delete'))
        if self.show_update_checkbox:
            update_tag = html_tpls['update'] % (name, name, name, _('Update'))

        # input and link to current file
        field_tag = html_tpls['field'] % (_('Change:'), input)
        link_tag = html_tpls['link'] % (_('Currently:'), settings.MEDIA_URL, value, value)

        return [u'<div>', link_tag, field_tag, delete_tag, update_tag, u'</div>']

    def value_from_datadict(self, data, files, name):
        # todo: do not allow both checkbox and file 
        #       (see django.forms.widget FILE_INPUT_CONTRADICTION)
        if data.get(u'%s_update' % name):
            value = u'__update__'
        elif data.get(u'%s_delete' % name):
            value = u'__delete__'
        else:
            value = super(DiverseFileInput, self).value_from_datadict(data, files, name)
        return value

    def render(self, name, value, attrs=None):
        input = super(DiverseFileInput, self).render(name, value, attrs)
        if value and hasattr(value, "url"):
            html_tpls = self.get_html_tpls(input, name, value, attrs)
            html_tags = self.get_html_tags(html_tpls, input, name, value, attrs)
            return mark_safe(u''.join(html_tags))
        else:
            return mark_safe(input)

class DiverseImageFileInput(DiverseFileInput):

    def __init__(self, thumbnail=None, **kwargs):
        super(DiverseImageFileInput, self).__init__(**kwargs)
        self.thumbnail = thumbnail

    def get_html_tpls(self, *args):
        tpls = super(DiverseImageFileInput, self).get_html_tpls(*args)
        tpls.update({'thumb': u'<div style="float: left; margin: 0 10px 0 0;">' \
                              u'<img src="%s" alt="%s" width="%s" height="%s"></div>',})
        return tpls

    def get_html_tags(self, html_tpls, input, name, value, attrs):
        tags = super(DiverseImageFileInput, self).get_html_tags(html_tpls, input, name, value, attrs)

        # get thumbnail tag
        thumbnail = self.thumbnail and getattr(value._container, self.thumbnail, None)
        if thumbnail:
            ttag = html_tpls['thumb'] % (thumbnail.url, thumbnail.name,
                                         thumbnail.width, thumbnail.height)
            tags.insert(1, ttag)

        return tags