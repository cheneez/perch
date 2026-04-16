from django import forms
from django.contrib.auth.models import User

from accounts.utils_profile import process_profile_image_upload

from .models import HOBBY_TAG_OPTIONS, StudentCompatibilitySurvey, StudentProfile


class StudentCreateProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].required = True

    class Meta:
        model = StudentProfile
        fields = [
            'first_name',
            'last_name',
            'school',
            'grade_year',
            'date_of_birth',
            'gender_identity',
            'gender_self_describe',
            'profile_picture',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_year': forms.Select(attrs={'class': 'form-select'}),
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


class StudentEditDetailsForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'username',
            'first_name',
            'last_name',
            'date_of_birth',
            'school',
            'grade_year',
            'gender_identity',
            'gender_self_describe',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_year': forms.Select(attrs={'class': 'form-select'}),
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
        sp_qs = StudentProfile.objects.filter(username__iexact=username)
        if self.instance.pk:
            sp_qs = sp_qs.exclude(pk=self.instance.pk)
        if sp_qs.exists():
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


class StudentEditProfileForm(forms.ModelForm):
    hobby_tags = forms.MultipleChoiceField(
        choices=HOBBY_TAG_OPTIONS,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'hobby-tag-check'}),
    )
    hobby_custom = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Add custom interests, comma-separated',
            }
        ),
    )
    remove_photo = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_remove_photo'}),
        initial='0',
    )

    class Meta:
        model = StudentProfile
        fields = [
            'profile_picture',
            'display_name',
            'bio',
            'employment_status',
            'current_role',
            'housing_budget',
            'can_contribute_rent',
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
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'current_role': forms.TextInput(attrs={'class': 'form-control'}),
            'housing_budget': forms.Select(attrs={'class': 'form-select'}),
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
            'can_contribute_rent': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            raw = self.instance.hobbies or []
            keys = {k for k, _ in HOBBY_TAG_OPTIONS}
            tags = [h for h in raw if h in keys]
            custom = [h for h in raw if h not in keys]
            self.initial.setdefault('hobby_tags', tags)
            self.initial.setdefault('hobby_custom', ', '.join(custom))

    def clean_profile_picture(self):
        f = self.cleaned_data.get('profile_picture')
        if not f:
            return f
        return process_profile_image_upload(f)

    def clean_remove_photo(self):
        return self.cleaned_data.get('remove_photo') == '1'

    def clean(self):
        data = super().clean()
        tags = data.get('hobby_tags') or []
        custom_raw = (data.get('hobby_custom') or '').strip()
        custom = [s.strip() for s in custom_raw.split(',') if s.strip()][:30]
        keys = {k for k, _ in HOBBY_TAG_OPTIONS}
        merged = list(dict.fromkeys(list(tags) + custom))
        data['hobbies_merged'] = merged
        return data

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.hobbies = self.cleaned_data.get('hobbies_merged', [])
        if self.cleaned_data.get('remove_photo'):
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)
            profile.profile_picture = None
        if commit:
            profile.save()
        return profile


class StudentCompatibilitySurveyForm(forms.ModelForm):
    class Meta:
        model = StudentCompatibilitySurvey
        fields = [
            'graduation_year',
            'major',
            'pets',
            'smoking_habits',
            'party_at_home',
            'sleep_schedule',
            'roommate_relationship',
            'morning_night_preference',
            'personality',
            'cleanliness',
            'guests',
            'noise_level',
            'study_at_home',
            'conflict_style',
        ]
        widgets = {field: forms.RadioSelect() for field in fields}
