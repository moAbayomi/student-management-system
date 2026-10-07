from django.shortcuts import render
from django.views.decorators.http import require_POST

from profiles.services import OnboardingService
from .forms import StyledSetPasswordForm


def onboard(request, token):
    """The link emailed to new teachers/students (guardians) to set their password."""
    profile = OnboardingService.find_profile(token)
    if profile is None:
        return render(request, 'users/onboarding/link_invalid.html', status=404)

    status = OnboardingService.status(profile)
    if status == 'already_active':
        return render(request, 'users/onboarding/done.html', {'username': profile.user.username})
    if status == 'expired':
        return render(request, 'users/onboarding/link_expired.html', {'token': token})

    form = StyledSetPasswordForm(profile.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        OnboardingService.complete(profile)
        return render(request, 'users/onboarding/done.html', {'username': profile.user.username})

    return render(request, 'users/onboarding/set_password.html', {
        'form': form,
        'username': profile.user.username,
    })


@require_POST
def resend_onboarding_link(request, token):
    # Keyed by the old token (not a profile id), so only someone who
    # received the original email can ask for a new one, and the new
    # link still goes to the email address on file.
    profile = OnboardingService.find_profile(token)
    if profile is None or OnboardingService.status(profile) != 'expired':
        return render(request, 'users/onboarding/link_invalid.html', status=404)

    sent = OnboardingService.regenerate_and_send(profile)
    return render(request, 'users/onboarding/link_sent.html', {'sent': sent})
