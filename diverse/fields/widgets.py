from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django import forms


class DiverseFileInput(forms.widgets.FileInput):
    """A AdminFileWidget that shows versions, delete and update checkboxes."""
    input_type = 'file'

    def __init__(self, attrs=None, show_version_links=True,
                 show_delete_checkbox=True, show_update_checkbox=True):
        super(DiverseFileInput, self).__init__(attrs=attrs)
        self.show_delete_checkbox = show_delete_checkbox
        self.show_update_checkbox = show_update_checkbox
        self.show_version_links = show_version_links

    def get_html_tpls(self, input, name, value, attrs):
        return {
            'open': u'<div style="overflow: auto;">',
            'close': u'</div>',
            'current': u"""
                {title}&nbsp;<a target="_blank" href="{url}">{value}</a>
            """,
            'field': u'<br>{title}&nbsp;{field}',
            'delete': u"""<nobr>
                <input type="checkbox" name="{name}_delete"
                                       id="id_{name}_delete"/> &mdash;
                <label style="display: inline; float: none;"
                       for="id_{name}_delete">{title}</label>
            </nobr>""",
            'update': u"""<nobr>
                <input type="checkbox" name="{name}_update"
                                       id="id_{name}_update"/> &mdash;
                <label style="display: inline; float: none;"
                       for="id_{name}_update">{title}</label>
            </nobr>""",
            'versions': u"""<div style="display: inline;">
                <a href="#" onclick="(function(elem){{
                    var ul = elem.parentNode.querySelector('ul');
                    if (ul.style.display == 'none') {{
                        ul.style.display = 'block';
                        elem.style.color = '#a41515';
                        elem.style.fontWeight = 'bold';
                    }} else {{
                        ul.style.display = 'none';
                        elem.style.color = null;
                        elem.style.fontWeight = null;
                    }}
                }})(this); return false;">{title}</a>
                <ul style="padding: 0; margin: 0; display: none;">{items}</ul>
            </div>""",
            'version': u"""<li>
                {name}: <a href="{url}" target="_blank">{url}</a>
            </li>""",
        }

    def get_html_tags(self, html_tpls, input, name, value, attrs):
        delete_tag, update_tag, versions_tag = (u'',) * 3

        # generate checkboxes
        if self.show_delete_checkbox:
            delete_tag = html_tpls['delete'].format(name=name,
                                                    title=_('Delete'))
        if self.show_update_checkbox:
            update_tag = html_tpls['update'].format(name=name,
                                                    title=_('Update'))

        # generate versions
        if self.show_version_links:
            versions_tag = html_tpls['versions'].format(
                title=_('Versions'), items=u'\n'.join(
                    html_tpls['version'].format(
                        url=value.dc.__getattr__(k)._get_url(), name=k.title())
                    for k in value.dc._versions.keys()
                ),
            )

        # input and link to current file
        field_tag = html_tpls['field'].format(title=_('Change:'), field=input)
        current_tag = html_tpls['current'].format(
            title=_('Currently:'), url=value.url, value=value)

        return [html_tpls['open'],
                current_tag, field_tag, delete_tag, update_tag, versions_tag,
                html_tpls['close'],]

    def value_from_datadict(self, data, files, name):
        # todo: do not allow both checkbox and file
        #       (see django.forms.widget FILE_INPUT_CONTRADICTION)
        if data.get(u'%s_update' % name):
            value = u'__update__'
        elif data.get(u'%s_delete' % name):
            value = u'__delete__'
        else:
            value = super(DiverseFileInput,
                          self).value_from_datadict(data, files, name)
        return value

    def render(self, name, value, attrs=None, renderer=None):
        input = super(DiverseFileInput, self).render(name, value, attrs)
        if value and hasattr(value, "url"):
            html_tpls = self.get_html_tpls(input, name, value, attrs)
            html_tags = self.get_html_tags(html_tpls,
                                           input, name, value, attrs)
            return mark_safe(u''.join(html_tags))
        else:
            return mark_safe(input)


class DiverseImageFileInput(DiverseFileInput):

    def __init__(self, thumbnail=None, **kwargs):
        super(DiverseImageFileInput, self).__init__(**kwargs)
        self.thumbnail = thumbnail

    def get_html_tpls(self, *args):
        tpls = super(DiverseImageFileInput, self).get_html_tpls(*args)
        tpls.update({
            'thumb': u"""<div style="float: left; margin: 0 10px 0 0;">
                <img src="{url}" alt="{alt}" width="{width}" height="{height}">
            </div>""",
        })
        return tpls

    def get_html_tags(self, html_tpls, input, name, value, attrs):
        tags = super(DiverseImageFileInput,
                     self).get_html_tags(html_tpls, input, name, value, attrs)

        # get thumbnail tag
        thumbnail = self.thumbnail and getattr(value._container,
                                               self.thumbnail, None)
        if thumbnail:
            img_tag = html_tpls['thumb'].format(
                url=thumbnail.url, alt=thumbnail.name,
                width=thumbnail.width, height=thumbnail.height)
            tags = [html_tpls['open'], img_tag,] + tags + [html_tpls['close'],]

        return tags
