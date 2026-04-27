from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from lessor.models import LessorProfile
from listings.models import Listing
from student.models import StudentProfile

from .forms import ReportForm
from notifications.models import Notification


REPORTABLE_MODELS = {
    ('listings', 'listing'): Listing,
    ('student', 'studentprofile'): StudentProfile,
    ('lessor', 'lessorprofile'): LessorProfile,
}


def _get_target_queryset(model, request):
    if model is Listing:
        return model.objects.accessible_to(request.user)
    return model.objects.all()


@login_required
def create_report(request, app_label, model, object_id):
    model = model.lower()
    model_class = REPORTABLE_MODELS.get((app_label, model))
    if model_class is None:
        raise Http404()

    target = get_object_or_404(_get_target_queryset(model_class, request), pk=object_id)
    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = ContentType.objects.get_for_model(target, for_concrete_model=False)
            report.object_id = target.pk
            report.save()

            safe_next = ''
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                safe_next = next_url
            Notification.objects.create(
                recipient=request.user,
                kind=Notification.Kind.REPORT_RECEIVED,
                title='Report received',
                body='Thanks — we received your report. Admins will review it soon.',
                link_url=safe_next,
            )
            messages.success(request, 'Your report has been submitted for review.')
            if safe_next:
                return redirect(safe_next)
            return redirect('landing')
    else:
        form = ReportForm(initial={'next': next_url})

    return render(
        request,
        'moderation/report_form.html',
        {
            'form': form,
            'target': target,
            'target_type': ContentType.objects.get_for_model(
                target,
                for_concrete_model=False,
            ).name,
        },
    )
