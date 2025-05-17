# Prompt pour créer une application d'export de wikis GitHub

Créez une application web Python qui permet aux utilisateurs d'exporter des wikis GitHub vers différents formats (Markdown, PDF, EPUB) avec les fonctionnalités suivantes:

## Architecture

Implémentez une architecture hexagonale (Ports and Adapters) avec CQRS et Event Sourcing:

- **Domain**: Modèles, interfaces de référentiels et services
- **Application**: Commandes, requêtes, gestionnaires d'événements et cas d'utilisation
- **Infrastructure**: Implémentations concrètes des référentiels et services
- **Interfaces**: API REST et interface web

## Fonctionnalités principales

1. **Gestion des wikis GitHub**:
   - Récupérer toutes les pages d'un wiki GitHub (pas seulement la page d'accueil)
   - Utiliser plusieurs stratégies pour trouver les pages (API, scraping HTML, recherche directe)
   - Gérer correctement les espaces, les caractères spéciaux et l'encodage URL

2. **Conversion de formats**:
   - Convertir le wiki en Markdown (conservant la structure)
   - Générer des fichiers PDF avec WeasyPrint
   - Créer des EPUB avec ebooklib
   - Utiliser Celery pour le traitement en arrière-plan

3. **Gestion des fichiers**:
   - Stocker les fichiers dans MinIO (compatible S3)
   - Générer des URLs de téléchargement temporaires

4. **Interface utilisateur**:
   - Page d'accueil permettant d'entrer une URL GitHub
   - Page de suivi de la progression des tâches en temps réel
   - Page listant tous les wikis exportés avec liens de téléchargement
   - Page de détail par tâche
   - Fonctionnalité de suppression des jobs et fichiers

5. **API REST**:
   - Endpoints pour créer des tâches d'export
   - Endpoints pour suivre la progression
   - Endpoints pour télécharger les fichiers
   - Endpoints pour supprimer des tâches et fichiers

## Stack technologique

- **Backend**: Python 3.11+ avec FastAPI
- **Interface**: Templates Jinja2 avec Tailwind CSS et DaisyUI
- **Base de données**: PostgreSQL via SQLAlchemy
- **Stockage de fichiers**: MinIO (compatible S3)
- **File d'attente**: Celery avec Redis
- **Conteneurisation**: Docker et Docker Compose

## Modèle de données

1. **WikiJob**:
   - ID
   - URL du dépôt
   - Statut (PENDING, PROCESSING, COMPLETED, FAILED)
   - Dates de création, mise à jour et complétion
   - Message d'erreur
   - Pourcentage de progression et message

2. **ExportFile**:
   - ID
   - ID du job
   - Format (MARKDOWN, PDF, EPUB)
   - Nom de fichier
   - Chemin de stockage
   - Taille en octets
   - Date de création

## Interface utilisateur détaillée

1. **Page d'accueil**:
   - Formulaire pour entrer l'URL d'un dépôt GitHub
   - Explication du processus d'export
   - Liens vers les autres pages

2. **Page de liste des tâches**:
   - Tableau avec toutes les tâches (URL, statut, progression, date)
   - Actualisation automatique
   - Lien vers la page de détail

3. **Page de détail d'une tâche**:
   - Informations sur le dépôt
   - Barre de progression
   - Statut actuel et messages
   - Téléchargement des fichiers générés
   - Option de suppression de la tâche et/ou des fichiers

4. **Page des wikis exportés**:
   - Tableau avec tous les wikis exportés
   - Boutons de téléchargement par format
   - Option de suppression

## Fonctionnalités avancées

1. **Gestion des erreurs**:
   - Récupération robuste en cas d'échec de l'API GitHub
   - Fallbacks et stratégies alternatives
   - Messages d'erreur explicites

2. **Suppression des ressources**:
   - Suppression d'un job et de tous ses fichiers associés
   - Suppression individuelle des fichiers générés
   - Confirmation avant suppression

3. **Interface réactive**:
   - Mise à jour en temps réel de la progression
   - Thème clair/sombre
   - Affichage responsive pour mobile et desktop

## Déploiement

- Utilisez Docker Compose pour orchestrer tous les services
- Configurez l'application via des variables d'environnement
- Fournissez un fichier .env.example comme modèle

## Documentation

- Instructions d'installation et d'utilisation
- Description des endpoints API
- Détail sur l'architecture hexagonale et CQRS/ES