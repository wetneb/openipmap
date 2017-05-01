from django import forms
from .tiling import max_2d_coord

class LocateForm(forms.Form):
    ip = forms.GenericIPAddressField()

class TileForm(forms.Form):
    x = forms.IntegerField(min_value=0, max_value=max_2d_coord)
    y = forms.IntegerField(min_value=0, max_value=max_2d_coord)
    zoom = forms.IntegerField(min_value=-32, max_value=32)
