from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from .forms import ProfileForm, SignUpForm
from .models import UserProfile


def signup(request):
    if request.user.is_authenticated:
        return redirect("collection:list")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user); return redirect("collection:list")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    collector_profile, _ = UserProfile.objects.select_related("favorite_species", "featured_card", "featured_card__set").get_or_create(user=request.user)
    items = request.user.collection_items.select_related("card", "card__set").prefetch_related("card__species")
    summary = items.aggregate(cards=Count("card", distinct=True), copies=Sum("quantity"))
    summary["species"] = items.filter(card__species__isnull=False).values("card__species").distinct().count()
    summary["wishlist"] = request.user.wishlist_items.count()
    recent_items = items.order_by("-updated_at")[:4]
    return render(request, "users/profile.html", {
        "summary": summary,
        "collector_profile": collector_profile,
        "recent_items": recent_items,
    })


@login_required
def profile_edit(request):
    collector_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=collector_profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil fue personalizado.")
            return redirect("users:profile")
    else:
        form = ProfileForm(instance=collector_profile, user=request.user)
    return render(request, "users/profile_edit.html", {"form": form, "collector_profile": collector_profile})
