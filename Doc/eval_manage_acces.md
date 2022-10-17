# Gestion de l'accès au site Web Cab

## But
Limiter l'accès au site Web Cab 

## Solutions possibles

| Description | Temps mise en place | Pour | Contre |
| ---      | ---      | ---      | --- |
| Blocage par Ip sur le serveur   | 5m + nb demande * 1m   | Rapide à mettre en place  |- Risque de s'enfermer dehors<br>- gestion manuel de Ip<br>- Action continuelle  |
| Authentification manuelle avec le fichier 'secret.tom' de streamlit   | 1d + nb demande * 1m   | +/- Rapide à mettre en place | - Gestion manuelle des utilisateurs <br>- Action continuelle<br>- Gestion de la perte de mot de passe (manuel ou à implémenter)|
| Authentification avec SSO Rénater  | 10d | - Accès par tous les membres de la fédération<br>- ¿Récupération de l'email utilisateur?  | -Site doit être accepté par Rénater<br>- Ajout personne extérieur plus compliqué |
| Authentification par Forge Mia | 7d |Accès par tous les membres de la fédération<br>- Gestion des accès par le projet Gitlab<br>- ¿Récupération de l'email utilisateur?<br>- ¿Envoie email à l'aide de mattermost?|¿Ajout personne extérieur plus compliqué?|

