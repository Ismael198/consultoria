from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from contas.forms import UserChangeForm
from perfil.forms import PerfilForm
from perfil.models import Perfil
from django.core.paginator import Paginator
from base.utils import filtrar_modelo
from forum.forms import PostagemForumForm
from contas.models import MyUser

def perfil_view(request, username):
    filtro = MyUser.objects.select_related('perfil').prefetch_related('user_postagem_forum')
    perfil = get_object_or_404(filtro, username=username)

    perfil_postagens = perfil.user_postagem_forum.all()  # Todas as postagens relacionadas com perfil
    filtros = {}

    valor_busca = request.GET.get("titulo")
    if valor_busca:
        filtros["titulo"] = valor_busca
        filtros["descricao"] = valor_busca
        perfil_postagens = filtrar_modelo(perfil_postagens, **filtros)

    form_list = [(postagem, PostagemForumForm(instance=postagem)) for postagem in perfil_postagens]

    paginacao = Paginator(form_list, 3)
    pagina_numero = request.GET.get("page")
    page_obj = paginacao.get_page(pagina_numero)

    form_dict = {postagem: form for postagem, form in page_obj}

    context = {'obj': perfil, 'page_obj': page_obj, 'form_dict': form_dict}
    return render(request, 'perfil.html', context)


@login_required
def editar_perfil(request, username):
    modelo_myuser = get_object_or_404(MyUser.objects.select_related('perfil'), username=username)
    redirect_route = request.POST.get('redirect_route', 'perfil')
    message = 'Seu Perfil foi atualizado com sucesso!'

    # Verifica se o usuário possui um perfil
    try:
        modelo_perfil = modelo_myuser.perfil
    except ObjectDoesNotExist:
        messages.error(request, 'O perfil associado a este usuário não existe.')
        return redirect('lista-postagem-forum')

    # Verifica permissões
    if request.user.username != modelo_myuser.username and not (
            request.user.groups.filter(name__in=['administrador', 'colaborador']).exists() or request.user.is_superuser
    ):
        messages.error(request, 'Você não tem permissão para editar este perfil.')
        return redirect('lista-postagem-forum')

    # Processa o formulário
    if request.method == 'POST':
        form_contas = UserChangeForm(request.POST, user=request.user, instance=modelo_myuser)
        form_perfil = PerfilForm(request.POST, request.FILES, instance=modelo_perfil)

        if form_perfil.is_valid() and form_contas.is_valid():
            form_contas.save()
            form_perfil.save()
            messages.success(request, message)
            return redirect(redirect_route)
    else:
        form_contas = UserChangeForm(user=request.user, instance=modelo_myuser)
        form_perfil = PerfilForm(instance=modelo_perfil)

    context = {'form_perfil': form_perfil, 'form_contas': form_contas, 'obj': modelo_myuser}
    return render(request, 'editar-perfil-form.html', context)