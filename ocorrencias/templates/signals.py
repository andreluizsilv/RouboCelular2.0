from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from .models import OcorrenciaCelular


@receiver(post_save, sender=OcorrenciaCelular)
def atualizar_search_vector_ocorrencia(sender, instance, created, **kwargs):
    """
    Sempre que um B.O. for salvo, recarrega o vetor de busca
    unindo dados do celular e do endereço associado.
    """
    if created or instance.search_vector is None:
        OcorrenciaCelular.objects.filter(pk=instance.pk).update(
            search_vector=(
                SearchVector('marca_celular', weight='A', config='portuguese') +
                SearchVector('num_bo', weight='A', config='portuguese') +
                SearchVector('endereco__logradouro', weight='B', config='portuguese') +
                SearchVector('endereco__bairro', weight='B', config='portuguese') +
                SearchVector('endereco__cidade', weight='C', config='portuguese') +
                SearchVector('delegacia_nome', weight='C', config='portuguese')
            )
        )