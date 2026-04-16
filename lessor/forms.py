from django import forms
from django.contrib.auth.models import User

from accounts.utils_profile import process_profile_image_upload

from .models import LessorProfile


class LessorCreateProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].required = True
        self.fields['email'].required = True

    class Meta:
        model = LessorProfile
        fields = [
            'first_name',
            'last_name',
            'email',
            'date_of_birth',
            'gender_identity',
            'gender_self_describe',
            'profile_picture',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender_identity': forms.Select(attrs={'class': 'form-select'}),
            'gender_self_describe': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(
                attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'id_profile_picture'}
            ),
        }

    def clean(self):
        data = super().clean()
        if data.get('gender_identity') == 'self_describe':
            if not (data.get('gender_self_describe') or '').strip():
                self.add_error(
                    'gender_self_describe',
                    'Please describe how you identify.',
                )
        return data

    def clean_profile_picture(self):
        f = self.cleaned_data.get('profile_picture')
        if not f:
            return f
        return process_profile_image_upload(f)


class LessorEditDetailsForm(forms.ModelForm):
    class Meta:
        model = LessorProfile
        fields = [
            'username',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender_identity',
            'gender_self_describe',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender_identity': forms.Select(attrs={'class': 'form-select'}),
            'gender_self_describe': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('Username is required.')
        qs = User.objects.filter(username__iexact=username)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('That username is already taken.')
        lp_qs = LessorProfile.objects.filter(username__iexact=username)
        if self.instance.pk:
            lp_qs = lp_qs.exclude(pk=self.instance.pk)
        if lp_qs.exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean(self):
        data = super().clean()
        if data.get('gender_identity') == 'self_describe':
            if not (data.get('gender_self_describe') or '').strip():
                self.add_error(
                    'gender_self_describe',
                    'Please describe how you identify.',
                )
        return data

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username = profile.username
            self.user.first_name = profile.first_name
            self.user.last_name = profile.last_name
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class LessorEditProfileForm(forms.ModelForm):
    remove_photo = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_remove_photo'}),
        initial='0',
    )

    def clean_remove_photo(self):
        return self.cleaned_data.get('remove_photo') == '1'

    class Meta:
        model = LessorProfile
        fields = [
            'profile_picture',
            'display_name',
            'bio',
            'email',
            'phone_number',
            'instagram',
            'linkedin',
            'handshake',
            'facebook',
            'show_email',
            'show_phone',
            'show_instagram',
            'show_linkedin',
            'show_handshake',
            'show_facebook',
        ]
        widgets = {
            'profile_picture': forms.FileInput(
                attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'id_profile_picture'}
            ),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'maxlength': 400}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'name@example.com'}
            ),
            'phone_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}
            ),
            'instagram': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '@yourhandle'}
            ),
            'linkedin': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/your-name'}
            ),
            'handshake': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'https://app.joinhandshake.com/...'}
            ),
            'facebook': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/your.profile'}
            ),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_instagram': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_linkedin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_handshake': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_facebook': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_profile_picture(self):
        f = self.cleaned_data.get('profile_picture')
        if not f:
            return f
        return process_profile_image_upload(f)

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.cleaned_data.get('remove_photo'):
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)
            profile.profile_picture = None
        if commit:
            profile.save()
        return profile
