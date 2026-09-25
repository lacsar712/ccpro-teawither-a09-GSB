from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from .forms import (
    GardenForm,
    LeafProvenanceForm,
    TroughForm,
    WitherBatchForm,
)
from .models import Garden, LeafProvenance, Trough, WitherBatch


def _wants_htmx(request):
    return request.headers.get("HX-Request") == "true"


@login_required
def home(request):
    context = {
        "garden_count": Garden.objects.count(),
        "trough_count": Trough.objects.count(),
        "batch_count": WitherBatch.objects.count(),
        "strip_count": LeafProvenance.objects.count(),
        # 各园溯源条数：与溯源列表按园过滤后的行数同一口径，用于对账
        "garden_strip_counts": Garden.objects.annotate(
            strip_count=Count("strips")
        ),
        "ready_count": Trough.objects.filter(status=Trough.STATUS_READY).count(),
        "withering_count": Trough.objects.filter(
            status=Trough.STATUS_WITHERING
        ).count(),
        "loading_count": Trough.objects.filter(
            status=Trough.STATUS_LOADING
        ).count(),
    }
    return render(request, "home.html", context)


# ---- Garden ----


class GardenListView(LoginRequiredMixin, ListView):
    model = Garden
    template_name = "gardens/list.html"
    context_object_name = "gardens"

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if _wants_htmx(request):
            html = render_to_string(
                "gardens/_table.html",
                {"gardens": self.object_list},
                request=request,
            )
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)


class GardenCreateView(LoginRequiredMixin, CreateView):
    model = Garden
    form_class = GardenForm
    template_name = "gardens/form.html"
    success_url = reverse_lazy("garden_list")

    def form_valid(self, form):
        messages.success(self.request, "茶园已创建")
        response = super().form_valid(form)
        if _wants_htmx(self.request):
            return redirect("garden_list")
        return response


class GardenUpdateView(LoginRequiredMixin, UpdateView):
    model = Garden
    form_class = GardenForm
    template_name = "gardens/form.html"
    success_url = reverse_lazy("garden_list")

    def form_valid(self, form):
        messages.success(self.request, "茶园已更新")
        return super().form_valid(form)


class GardenDeleteView(LoginRequiredMixin, DeleteView):
    model = Garden
    template_name = "gardens/confirm_delete.html"
    success_url = reverse_lazy("garden_list")

    def form_valid(self, form):
        # 仍有茶青溯源条的茶园拒绝删除（模型层同为 PROTECT）
        strip_count = self.object.strips.count()
        if strip_count:
            messages.error(
                self.request,
                f"茶园「{self.object.name}」仍有 {strip_count} 条茶青溯源，"
                "已拒绝删除。",
            )
            return redirect("garden_list")
        messages.success(self.request, "茶园已删除")
        return super().form_valid(form)


# ---- Trough ----


class TroughListView(LoginRequiredMixin, ListView):
    model = Trough
    template_name = "troughs/list.html"
    context_object_name = "troughs"

    def get_queryset(self):
        return Trough.objects.select_related("garden").all()

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if _wants_htmx(request):
            html = render_to_string(
                "troughs/_table.html",
                {"troughs": self.object_list},
                request=request,
            )
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)


class TroughCreateView(LoginRequiredMixin, CreateView):
    model = Trough
    form_class = TroughForm
    template_name = "troughs/form.html"
    success_url = reverse_lazy("trough_list")

    def form_valid(self, form):
        messages.success(self.request, "萎凋槽已创建")
        return super().form_valid(form)


class TroughUpdateView(LoginRequiredMixin, UpdateView):
    model = Trough
    form_class = TroughForm
    template_name = "troughs/form.html"
    success_url = reverse_lazy("trough_list")

    def form_valid(self, form):
        messages.success(self.request, "萎凋槽已更新")
        return super().form_valid(form)


class TroughDeleteView(LoginRequiredMixin, DeleteView):
    model = Trough
    template_name = "troughs/confirm_delete.html"
    success_url = reverse_lazy("trough_list")

    def form_valid(self, form):
        messages.success(self.request, "萎凋槽已删除")
        return super().form_valid(form)


# ---- WitherBatch ----


class BatchListView(LoginRequiredMixin, ListView):
    model = WitherBatch
    template_name = "batches/list.html"
    context_object_name = "batches"

    def get_queryset(self):
        return WitherBatch.objects.select_related("trough", "trough__garden").all()

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if _wants_htmx(request):
            html = render_to_string(
                "batches/_table.html",
                {"batches": self.object_list},
                request=request,
            )
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)


class BatchCreateView(LoginRequiredMixin, CreateView):
    model = WitherBatch
    form_class = WitherBatchForm
    template_name = "batches/form.html"
    success_url = reverse_lazy("batch_list")

    def form_valid(self, form):
        messages.success(self.request, "萎凋批次已创建")
        return super().form_valid(form)


class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = WitherBatch
    form_class = WitherBatchForm
    template_name = "batches/form.html"
    success_url = reverse_lazy("batch_list")

    def form_valid(self, form):
        messages.success(self.request, "萎凋批次已更新")
        return super().form_valid(form)


class BatchDeleteView(LoginRequiredMixin, DeleteView):
    model = WitherBatch
    template_name = "batches/confirm_delete.html"
    success_url = reverse_lazy("batch_list")

    def form_valid(self, form):
        messages.success(self.request, "萎凋批次已删除")
        return super().form_valid(form)


# ---- LeafProvenance（茶青溯源条） ----


class StripListView(LoginRequiredMixin, ListView):
    model = LeafProvenance
    template_name = "strips/list.html"
    context_object_name = "strips"

    def get_queryset(self):
        qs = LeafProvenance.objects.select_related(
            "garden", "batch", "batch__trough"
        )
        garden = self.request.GET.get("garden")
        if garden:
            qs = qs.filter(garden_id=garden)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gardens"] = Garden.objects.all()
        context["active_garden"] = self.request.GET.get("garden", "")
        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if _wants_htmx(request):
            html = render_to_string(
                "strips/_table.html",
                {"strips": self.object_list},
                request=request,
            )
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)


class StripCreateView(LoginRequiredMixin, CreateView):
    model = LeafProvenance
    form_class = LeafProvenanceForm
    template_name = "strips/form.html"
    success_url = reverse_lazy("strip_list")

    def form_valid(self, form):
        messages.success(self.request, "茶青溯源条已创建")
        return super().form_valid(form)


class StripUpdateView(LoginRequiredMixin, UpdateView):
    model = LeafProvenance
    form_class = LeafProvenanceForm
    template_name = "strips/form.html"
    success_url = reverse_lazy("strip_list")

    def form_valid(self, form):
        messages.success(self.request, "茶青溯源条已更新")
        return super().form_valid(form)


class StripDeleteView(LoginRequiredMixin, DeleteView):
    model = LeafProvenance
    template_name = "strips/confirm_delete.html"
    success_url = reverse_lazy("strip_list")

    def form_valid(self, form):
        messages.success(self.request, "茶青溯源条已删除")
        return super().form_valid(form)
