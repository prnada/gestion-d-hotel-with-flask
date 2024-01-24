var ctx = document.getElementById('myChart').getContext('2d');
var pourcentage_commentaires_positifs = nb_commentaires_positifs * 100;
var pourcentage_commentaires_negatifs = nb_commentaires_negatifs * 100;
var myChart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: ['Commentaires positifs', 'Commentaires négatifs'],
        datasets: [{
            label: 'Répartition des commentaires',
            data: [pourcentage_commentaires_positifs, pourcentage_commentaires_negatifs],
            backgroundColor: [
                'green',
                'red'
            ],
            borderColor: [
                'white',
                'white'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        legend: {
            position: 'bottom',
            labels: {
                fontColor: 'white'
            }
        }
    }
});