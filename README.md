Pyhton Programmation Linéaire Solveur

Réalisé par — Groupe 8 (3IIR8)
-Baraka Nada
-Kamili Farah
-Khancha Ilyas

Encadré par
-M. Abdelati REHA
-M. Yassine SAFSOUF

Année Universitaire
2025 – 2026

1-Présentation du projet
Ce projet a été réalisé dans le cadre du module de Programmation Linéaire et a pour objectif de développer une application permettant de résoudre des problèmes d’optimisation liés à la gestion des chambres d’un hôtel.
L’application permet de modéliser un programme linéaire, définir les contraintes et calculer automatiquement la solution optimale afin de maximiser le revenu de l’établissement.

Deux méthodes de résolution ont été implémentées :
-La méthode graphique
-La méthode du simplexe

Le projet met également en pratique plusieurs notions d’informatique telles que :
-la programmation orientée objet,
-le développement Python,
-l’automatisation des calculs,
-la visualisation des résultats.
-Fonctionnalités principales

L’application permet de :
-Saisir les variables de décision
-Définir la fonction objectif
-Ajouter les contraintes du problème
-Résoudre automatiquement le programme linéaire
-Utiliser la méthode graphique pour les problèmes à deux variables
-Utiliser la méthode du simplexe pour les problèmes complexes
-Afficher les tableaux du simplexe étape par étape
-Générer les graphiques de la région réalisable
-Afficher la solution optimale et la valeur maximale de l’objectif

2-Technologies utilisées
-Langages
		-Python
		-HTML
		-CSS
		-JavaScript
-Bibliothèques et outils
		-Matplotlib
		-Flask
		-Programmation Orientée Objet (POO)

3-Structure du projet
lp_solver/
│
├── app.py
├── requirements.txt
│
├── models/
│   ├── linear_program.py
│   ├── constraint.py
│   └── solution.py
│
├── solvers/
│   ├── simplex_solver.py
│   └── graphical_solver.py
│
├── routes/
│   └── main.py
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/style.css
    └── js/app.js

4-Méthodes utilisées
-Méthode graphique
La méthode graphique est utilisée pour les problèmes contenant deux variables de décision. Elle permet de représenter graphiquement les contraintes et de déterminer la région réalisable ainsi que la solution optimale.

-Méthode du simplexe
La méthode du simplexe permet de résoudre des problèmes comportant plusieurs variables et contraintes. L’algorithme effectue des itérations successives afin d’atteindre la solution optimale.

5-Exécution du projet
*Installation des dépendances
pip install -r requirements.txt

*Lancement de l’application
python app.py

 *Accès à l’application
http://localhost:5000

6-Résultats obtenus
L’application permet d’obtenir automatiquement :
les valeurs optimales des variables,
la valeur maximale du revenu,
les tableaux intermédiaires du simplexe,
les représentations graphiques des contraintes.

Les résultats obtenus sont conformes aux calculs réalisés manuellement et aux validations effectuées avec le solveur d’Excel.

7-Conclusion
Ce projet a permis d’appliquer les concepts de programmation linéaire à un cas concret d’optimisation dans le secteur hôtelier.
L’implémentation informatique réalisée en Python a permis d’automatiser les calculs et de simplifier la résolution des problèmes d’optimisation tout en améliorant la fiabilité et la rapidité des résultats.
Ce travail constitue également une introduction pratique à l’utilisation des outils informatiques dans l’aide à la décision et l’optimisation des ressources.