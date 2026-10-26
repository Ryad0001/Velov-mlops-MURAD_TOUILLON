{#
    Échoue quand la part de lignes où column_name dépasse capacity_column est supérieure à max_share.
    Renvoie une seule ligne (le décompte) : le seuil est une proportion, il ne dépend pas du volume.
    max_share = 0 : la moindre ligne au-dessus de la capacité fait échouer le test.
#}
{% test within_capacity(model, column_name, capacity_column='capacity', max_share=0) %}

select
    count(*) filter (where {{ column_name }} > {{ capacity_column }}) as n_over_capacity,
    count(*) as n_rows
from {{ model }}
having count(*) filter (where {{ column_name }} > {{ capacity_column }}) > {{ max_share }} * count(*)

{% endtest %}
