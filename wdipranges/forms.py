from django import forms
from .tiling import max_2d_coord
import netaddr
from .utils import to_q

class LocateForm(forms.Form):
    ip = forms.GenericIPAddressField()

class ReverseForm(forms.Form):
    x = forms.IntegerField(min_value=0, max_value=max_2d_coord)
    y = forms.IntegerField(min_value=0, max_value=max_2d_coord)

class TileForm(forms.Form):
    x = forms.IntegerField(min_value=0, max_value=max_2d_coord)
    y = forms.IntegerField(min_value=0, max_value=max_2d_coord)
    zoom = forms.IntegerField(min_value=-32, max_value=32)

class PushRangesForm(forms.Form):
    qid = forms.CharField()
    ipranges = forms.CharField()

    def clean_qid(self):
        qid = to_q(self.cleaned_data['qid'])
        if not qid:
            raise forms.ValidationError('Invalid QID')
        return qid

    def clean_ipranges(self):
        ranges = self.cleaned_data['ipranges'].split(', ')
        try:
            converted = list(map(netaddr.IPNetwork, ranges))
            return converted
        except netaddr.core.AddrFormatError:
            raise forms.ValidationError('Invalid IP range')

