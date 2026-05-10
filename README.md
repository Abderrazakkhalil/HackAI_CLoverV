

```markdown
# 🚀 Guide d'installation pour l'équipe (Setup)

Pour que toute l'équipe soit synchronisée sur la même configuration MLOps et éviter les erreurs de version, suivez ces étapes dans votre terminal VSCode :

### 1. Cloner le projet
```bash
git clone [https://github.com/ton-username/HackAI_CLoverV.git](https://github.com/ton-username/HackAI_CLoverV.git)
cd HackAI_CLoverV

```

### 2. Créer l'environnement virtuel

Il est impératif d'utiliser un environnement isolé pour ne pas corrompre vos installations globales.

```bash
python -m venv venv

```

### 3. Activer l'environnement

* **Sur Windows :**
```bash
.\venv\Scripts\activate

```


* **Sur Mac/Linux :**
```bash
source venv/bin/activate

```



*(Vous devriez voir `(venv)` apparaître au début de votre ligne de commande).*

### 4. Installer les dépendances

```bash
pip install -r requirements.txt

```

### 5. Configurer les variables d'environnement (API Keys)

Pour des raisons de sécurité, les clés ne sont pas sur GitHub.

1. Dupliquez le fichier `.env.example`.
2. Renommez la copie en `.env`.
3. Ouvrez le fichier `.env` et remplissez les valeurs (Hugging Face, Gemini, Groq, W&B) avec les clés qui vous ont été envoyées en privé.

---

**💡 Note Tech Lead :** Ne "pushez" jamais votre fichier `.env`. Il est déjà listé dans le `.gitignore` pour votre sécurité. Pour toute nouvelle bibliothèque installée, n'oubliez pas de mettre à jour le fichier avec `pip freeze > requirements.txt`.

```

***

### Prochaines étapes pour toi (Tech Lead) :
1.  Ouvre ton `README.md` dans VSCode.
2.  Colle ce texte.
3.  Remplace `ton-username` dans le lien `git clone` par ton vrai nom d'utilisateur GitHub.
4.  Fais un `git add README.md`, `git commit -m "docs: add setup instructions for the team"`, et `git push`.


```
