MOZA Active Pedal — intégration interface + télémétrie (v1.5 — intégration Automobilista 2)

CONTENU
- moza_ui.pyw : interface de configuration (sans console sous Windows).
- moza_controller.py : programme principal pour les jeux intégrés, avec sélection du détecteur LMU par classe.
- moza_protocol.py : trames MOZA capturées, conservées telles quelles.
- forza_horizon_6.py : réception et décodage de la télémétrie UDP officielle FH6.
- raceroom_telemetry.py : lecture de la mémoire partagée officielle RaceRoom (API 3.6+).
- ams2_telemetry.py : lecture de la mémoire partagée AMS2 (format Project CARS 2, version 14).
- test_ams2_telemetry.py : tests synthétiques du décodeur AMS2.
- moza_settings.json : créé par l'interface après enregistrement.

INSTALLATION
1. Place tous les fichiers du dossier dans le même répertoire.
2. Installe les dépendances : py -m pip install -r requirements.txt
3. Lance moza_ui.pyw pour régler le jeu, le port COM et les alertes.
4. Clique sur « Enregistrer les paramètres ».
5. Lance le programme principal : py moza_controller.py

IMPORTANT
- Le programme principal lit moza_settings.json au démarrage. Ferme-le puis relance-le
  après toute modification des paramètres.
- Les fréquences disponibles sont 10, 20, 30, 40, 50, 60, 70, 80, 90 et 100 Hz.
- Chaque alerte utilise sa propre fréquence et son intensité configurées.
- L'avertissement préventif fonctionne sur LMU, AC et ACR. La vitesse télémétrique
  est corrigée par le grip estimé : vitesse_effective = vitesse * max(0, 1 - k *
  glissement_max). Le glissement maximal des quatre roues est borné entre 0 et 1.
  Le coefficient k est réglable de 0 à 3 dans l'onglet Avancé ; sa valeur par défaut
  est 0 (aucune correction). À 1, la correction est proportionnelle au glissement ;
  au-delà de 1, elle est amplifiée. La vitesse minimale d'activation est comparée
  à la vitesse réelle du véhicule, avant correction.
- Les réglages sont séparés en profils indépendants : LMU, AC, ACR, FH6, iRacing, F1 26, AC EVO, RaceRoom et AMS2.
  Le changement de jeu dans l'interface charge immédiatement son profil. Les alertes,
  paramètres avancés et paramètres généraux (dont port COM et fréquences) sont propres
  à chaque profil. Le contrôleur charge uniquement le profil du jeu sélectionné.
  L'ancien fichier mono-profil est migré vers le jeu qui y était sélectionné.
- Si « Activer le système de vibrations » est décoché, la télémétrie peut toujours
  être lue mais aucune vibration n'est envoyée.
- Ne lance pas simultanément le test matériel de l'interface et le programme principal :
  ils ne doivent pas ouvrir le même port COM en même temps.
- Conserver moza_protocol.py à côté des deux scripts : les trames ne sont pas générées
  mathématiquement, elles proviennent des captures réalisées dans Pit House.

VÉRIFICATIONS EFFECTUÉES
- Compilation syntaxique des deux scripts Python.
- Tests numériques de la correction de vitesse par le grip et du coefficient.
- Vérification syntaxique et statique du chargement / sauvegarde des profils.
- Compatibilité de migration depuis l'ancien fichier mono-profil.
- Le matériel MOZA et les jeux n'ont pas été testés depuis cet environnement.

FORZA HORIZON 6 — CONFIGURATION
1. Dans FH6 : Paramètres > HUD et gameplay > Data Out : Activé.
2. Adresse IP Data Out : 127.0.0.1.
3. Port Data Out : même valeur que « Port UDP FH6 » dans le profil FH6
   de l'interface MOZA (valeur initiale : 20444).
4. Enregistrer le profil FH6 dans l'interface, puis lancer moza_controller.py.
5. Les paquets ne sont envoyés que pendant la conduite. En menu ou en pause,
   le contrôleur attend sans déclencher d'alerte.

Le décodeur attend les paquets FH6 de 324 octets (little-endian).
Il récupère Speed (m/s, converti en km/h), Brake (0..255, normalisé)
et les quatre TireSlipRatio (magnitude bornée à 0..1 pour le détecteur).
Les valeurs TireSlipAngle et TireCombinedSlip sont également décodées et
conservées dans les données du module pour les analyses ultérieures.


LE MANS ULTIMATE — DÉTECTION PAR CLASSE (v0.9)
- La classe est lue directement dans le champ mVehicleClass de TelemInfoV01.
- HYP (Hypercar) : conservation de la détection historique basée sur mGripFract.
- LMP2_ELMS, LMP2, LMP3 et GTE : nouvelle estimation du glissement longitudinal
  par roue, à partir de |mRotation| * mStaticUndeflectedRadius et
  |mLongitudinalGroundVel|.
- GT3 : détection de blocage et prédiction désactivées volontairement pour cette
  version. L'avertissement préventif de freinage reste disponible.
- Les classes non reconnues restent sans détection de blocage afin d'éviter les
  faux positifs.
- Le contrôleur affiche la classe et la méthode sélectionnée dans la console.
- Le détecteur HYP existant n'a pas été modifié. Les profils AC, ACR et FH6
  conservent leur traitement antérieur.

À TESTER
- Valider en piste la sélection HYP / LMP2 / LMP3 / GTE.
- Comparer le glissement calculé aux blocages réels sur LMP2 et LMP3.
- Les seuils communs restent ceux du profil LMU ; aucune calibration par classe
  n'est introduite dans cette version.


VERSION 1.0 — AVERTISSEMENT DE FREINAGE PAR CLASSE LMU

- L'onglet Avancé contient maintenant une section "Classes LMU" avec des réglages indépendants pour HYP, LMP2 ELMS, LMP2, LMP3, GTE et GT3.
- Chaque classe dispose de son activation, fréquence, intensité maximale et paramètres de courbe.
- La GT3 peut donc utiliser l'avertissement préventif même si sa détection de blocage reste désactivée.
- Le seuil de début n'expose plus sa pente : celle-ci est calculée automatiquement avec A = valeur de début à 0 km/h et Vmax choisi : pente = (100 - A) / Vmax. À Vmax, le seuil de début atteint 100 % de demande de freinage, donc l'avertissement préventif ne peut plus se déclencher.
- Les réglages communs aux autres jeux restent dans leurs profils et ne sont pas affectés par les réglages de classes LMU.
- Les anciennes configurations sont migrées avec des valeurs par défaut par classe.


VERSION 1.1 — AVERTISSEMENT PREVENTIF GLOBAL + SURCHARGES LMU

- Les réglages généraux de l'avertissement préventif (activation, fréquence, intensité et courbe) sont désormais partagés par tous les jeux : AC, ACR, FH6 et LMU.
- Dans LMU, lorsqu'une classe connue est détectée (HYP, LMP2 ELMS, LMP2, LMP3, GTE ou GT3), ses réglages dédiés remplacent les réglages généraux.
- Si la classe LMU est inconnue ou non reconnue, les réglages généraux sont utilisés au lieu de désactiver l'avertissement.
- Les paramètres de blocage confirmé et de prédiction restent indépendants de l'avertissement préventif.
- Les anciens fichiers de configuration sont migrés : les valeurs générales sont initialisées à partir du profil sélectionné et les réglages par classe LMU existants sont conservés.


VERSION 1.2 — INTÉGRATION iRACING + F1 26 (PC)

iRACING
- Connexion à la mémoire partagée officielle iRacing via le paquet Python pyirsdk.
- Installation : exécuter `pip install -r requirements.txt` dans l'environnement Python de l'application.
- Lancer iRacing et entrer dans la voiture ; le contrôleur attend automatiquement que le SDK soit disponible.
- Variables lues : Speed, Brake, Throttle, LFspeed, RFspeed, LRspeed et RRspeed.
- Speed et vitesses de roue sont exprimées en m/s. Le glissement de freinage par roue est estimé par
  max(0, (|Speed| - |WheelSpeed|) / |Speed|), avec garde-fou sous 3 m/s.
- La lecture est limitée au rythme du SDK (60 Hz). La disponibilité des variables est vérifiée à la connexion.

F1 26
- Réception UDP du format 2026 uniquement ; le format 2024/2025 n'est pas accepté.
- Dans F1 26, activer la télémétrie UDP, choisir le format 2026, l'adresse IP 127.0.0.1
  et le port identique au réglage « Port UDP F1 26 » de l'application (défaut : 20777).
- Régler la fréquence d'envoi selon la valeur proposée par le jeu (60 Hz conseillé pour les essais).
- Le lecteur associe les paquets Car Telemetry (ID 6) et Motion Ex (ID 13) à partir de leur
  identifiant de trame. Il lit la vitesse, le frein, l'accélérateur et les données individuelles
  wheelSpeed / wheelSlipRatio des quatre roues.
- Les tableaux de roues F1 sont dans l'ordre RL, RR, FL, FR. Le détecteur commun consomme les
  quatre taux de glissement dans cet ordre ; il n'a pas besoin d'un ordre gauche/droite spécifique.

LIMITES DE VALIDATION v1.2
- Les lecteurs iRacing et F1 26 ont été testés avec des paquets / valeurs synthétiques et
  compilés syntaxiquement. Ils n'ont pas encore été testés dans une session réelle.
- Pour iRacing, la formule basée sur Speed et LF/RF/LR/RRspeed est une estimation à valider
  en piste selon les voitures et les unités/valeurs publiées par le SDK.
- Pour F1 26, le lecteur exige que les deux types de paquets arrivent avec le même frame ID.
  En cas de pertes UDP, il attend une paire complète avant d'alimenter le détecteur.


VERSION 1.3 — ASSETTO CORSA EVO (PC)

- Ajout d'un profil indépendant ACEVO dans l'interface.
- Lecture read-only de la page Windows `Local\acevo_pmf_physics`.
- La page physique est lue à chaque pas de lecture configuré (333 Hz par défaut).
- Champs utilisés : packetId, gas, brake, speedKmh et slipRatio par roue.
- Champs diagnostiques conservés : wheelSlip combiné, wheelLoad, wheelAngularSpeed et absInAction.
- Ordre des roues : FL, FR, RL, RR.
- Le détecteur commun reçoit la magnitude de slipRatio par roue, bornée entre 0 et 1.
  Les valeurs brutes signées restent disponibles dans le lecteur pour calibration.
- Aucune dépendance Python supplémentaire : lecture directe via Win32 et struct.
- L'avertissement préventif utilise les réglages généraux ; les remplacements par classe
  restent propres à LMU et ne sont pas appliqués à AC EVO.

CONFIGURATION ASSETTO CORSA EVO
1. Démarrer Assetto Corsa EVO et entrer dans une session de conduite (pas seulement le menu).
2. Dans MOZA Integration, sélectionner « Assetto Corsa EVO ».
3. Choisir la fréquence de lecture (333 Hz par défaut), enregistrer et lancer le contrôleur.
4. La connexion attend la présence de `Local\acevo_pmf_physics` et réessaie automatiquement.

VALIDATION
- Tests synthétiques du décodage des offsets physiques et de l'ordre des quatre roues.
- Compilation syntaxique des modules et du contrôleur.
- Pas de test réel dans Assetto Corsa EVO ni sur pédale MOZA depuis cet environnement.
- Les seuils de slipRatio et leur comportement réel en freinage doivent être validés en piste.


VERSION 1.4 — RACEROOM RACING EXPERIENCE (PC)

- Ajout d'un profil indépendant « RaceRoom Racing Experience » (R3E).
- Connexion en lecture seule à la mémoire partagée Windows « $R3E ».
- Le lecteur vérifie la version majeure/mineure et l'offset de structure avant
  d'interpréter les données. Les layouts différents sont refusés pour éviter
  de décoder silencieusement des valeurs erronées. API minimale prise en charge : 3.6.
- Données utilisées : vitesse véhicule, accélérateur, frein, vitesse linéaire de
  chaque roue, vitesse angulaire, grip télémétrique, pression de frein et charge pneu.
- L'ordre des roues est FL, FR, RL, RR. Le glissement de freinage est estimé à partir
  de la différence entre la vitesse du véhicule et la vitesse linéaire de chaque roue.
- Aucune dépendance Python supplémentaire n'est nécessaire.

CONFIGURATION RACEROOM
1. Démarrer RaceRoom et entrer dans une session de conduite.
2. Dans MOZA Integration, sélectionner « RaceRoom Racing Experience ».
3. Enregistrer les paramètres puis lancer moza_controller.py.
4. La console doit afficher « RaceRoom shared memory connected (API 3.6+) ».

LIMITES ET VALIDATION
- La documentation officielle définit tire_speed comme la vitesse linéaire de roue
  en m/s et tire_rps comme sa vitesse angulaire en rad/s. Le lecteur utilise tire_speed
  pour estimer le glissement longitudinal au freinage ; tire_rps est conservé pour
  diagnostic. Le comportement réel doit être vérifié en piste.
- Les identifiants de classe et le nom du véhicule sont exposés à titre diagnostique ;
  aucune calibration spécifique par classe RaceRoom n'est appliquée.
- Compilation Python et tests synthétiques du décodage effectués. Aucun test en jeu
  ni test matériel MOZA n'a été effectué depuis cet environnement.


VERSION 1.5 — AUTOMOBILISTA 2 (PC)

- Ajout d'un profil indépendant « Automobilista 2 » (AMS2).
- Connexion en lecture seule à la mémoire partagée Windows « $pcars2$ ».
- Dans AMS2, régler Options > System > Shared Memory sur « Project CARS 2 ».
- Le lecteur vérifie la version de mémoire partagée 14 et utilise mSequenceNumber
  pour éviter de lire une page pendant que le jeu la met à jour.
- Données lues : mSpeed, mBrake, mThrottle, mAntiLockActive, mTyreRPS,
  mTyreFlags, mTyreSlipSpeed et mTyreGrip. Les deux derniers champs sont
  marqués OBSOLETE dans l'en-tête et sont conservés uniquement à des fins
  de diagnostic ; ils ne servent pas au calcul du glissement.
- Ordre des roues : FL, FR, RL, RR.
- En l'absence d'un canal de vitesse linéaire par roue documenté comme actif,
  le lecteur calcule un déficit relatif de vitesse angulaire :
  slip_i = 1 - |RPS_i| / max(|RPS_4 roues|), borné entre 0 et 1.
  Ce signal est une comparaison entre roues, pas un taux physique absolu de
  glissement longitudinal. Il doit être validé en piste, notamment en virage.
- La lecture est plafonnée à 200 Hz, le jeu actualisant la mémoire à chaque
  image et pouvant publier jusqu'à environ 200 Hz selon la configuration.
- Aucune dépendance Python supplémentaire n'est nécessaire.

CONFIGURATION AUTOMOBILISTA 2
1. Démarrer AMS2 et ouvrir Options > System.
2. Régler Shared Memory sur « Project CARS 2 », puis appliquer le réglage.
3. Entrer dans une session de conduite.
4. Dans MOZA Integration, sélectionner « Automobilista 2 ».
5. Enregistrer les paramètres et lancer moza_controller.py.
6. La console doit afficher « Automobilista 2 shared memory connected ».

VALIDATION AMS2
- Compilation syntaxique Python effectuée.
- Cinq tests synthétiques du décodage, de l'ordre des roues, du filtrage des
  séquences dupliquées / en cours d'écriture et du rejet d'une version inconnue
  ont réussi.
- Aucun test réel dans AMS2 ni sur le matériel MOZA n'a été effectué depuis
  cet environnement. Le calcul relatif basé sur mTyreRPS doit être validé
  en ligne droite puis en virage avant d'ajuster les seuils.


MISE À JOUR — USURE DES PNEUS MULTI-JEUX (PHF)

Le coefficient « Influence de l'usure des pneus » agit maintenant sur les jeux
pour lesquels la télémétrie fournit une mesure exploitable par roue :
- Le Mans Ultimate : mWear (fraction usée, 0 = neuf, 1 = usé), déjà pris en charge.
- Automobilista 2 : mTyreWear (fraction usée, 0 = neuf, 1 = usé).
- iRacing : moyenne des trois zones de bande de roulement L/M/R, convertie
  depuis le pourcentage restant vers une fraction usée.
- F1 26 : paquet Car Damage (ID 10), m_tyresWear (pourcentage usé).

Le coefficient est commun aux jeux dans l'avertissement préventif global ;
les réglages par classe LMU restent prioritaires pour LMU. Sa valeur 0 désactive
l'influence de l'usure. Le facteur utilisé est : 1 - coefficient * usure_max.

LIMITES DE DISPONIBILITÉ
- Forza Horizon 6 : le format Data Out FH6 ne transmet pas TireWear.
- RaceRoom : l'API de mémoire partagée utilisée expose l'activation de l'usure,
  mais pas une mesure d'usure individuelle des quatre pneus.
- Assetto Corsa EVO : le champ tyreWear de la mémoire partagée est signalé comme
  non alimenté dans les versions actuellement documentées ; il n'est pas utilisé.
- Assetto Corsa : tyreWear existe, mais se comporte comme un indicateur de santé/grip
  non linéaire et dépendant de la mise en température ; il n’est pas assimilé à une
  dégradation monotone dans cette version.
- Assetto Corsa Rally : aucune mesure d’usure par roue suffisamment documentée
  n’a été identifiée pour cette intégration.

Sans donnée wheel_wear fournie par le jeu, le facteur d'usure reste neutre :
aucune valeur fictive n'est substituée. Les jeux et le matériel PHF n'ont pas
été testés en conditions réelles depuis cet environnement.


INTÉGRATION — ASSETTO CORSA COMPETIZIONE (ACC)

- Ajout d'un profil ACC indépendant dans les deux interfaces de configuration.
- Lecture en mémoire partagée Windows, en lecture seule :
  Local\\acpmf_physics et Local\\acpmf_static.
- Le lecteur dédié acc_telemetry.py récupère la vitesse, la demande de frein,
  les vitesses angulaires et le tableau slipRatio des quatre roues.
- Ordre des roues : FL, FR, RL, RR.
- ACC fournit slipRatio signé : le glissement de freinage est négatif et le
  glissement d'accélération positif. Le lecteur transmet max(0, min(1, -slipRatio))
  au détecteur commun.
- Le champ tyreRadius de la page statique est indiqué comme non utilisé par ACC ;
  il n'est donc pas utilisé pour reconstruire artificiellement le slip.
- Les seuils minimum/maximum, la prédiction, les intensités et fréquences
  utilisent le profil ACC propre au jeu. Les autres profils ne sont pas modifiés.
- ACC partage les noms de mémoire acpmf_* avec Assetto Corsa ; le contrôleur
  n'ouvre que les pages correspondant au jeu sélectionné.
- La télémétrie d'usure ACC n'est pas encore utilisée dans l'avertissement
  préventif : seul le signal de freinage/slip est intégré.

VALIDATION ACC
- Tests synthétiques du calcul de slip : égalité vitesse roue/véhicule,
  roue bloquée, roue plus rapide, ordre des roues et garde-fou basse vitesse.
- Compilation syntaxique des modules Python.
- La connexion à une session ACC réelle et la cohérence des rayons statiques
  doivent encore être validées sur le PC de l'utilisateur.
