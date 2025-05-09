# Compte-rendu TP5 - Systèmes de Détection d'Intrusion

## Plan de bataille pour la détection d'un ransomware

Pour détecter efficacement un scénario d'attaque par ransomware, nous avons élaboré un plan centré sur les points critiques suivants :

### Étape 2 : Détection du téléchargement de fichiers suspects
- **Proxy HTTP (Squid)** : Filtrage des téléchargements selon le type de fichier et blocage des domaines malveillants
- **NIDS (Suricata)** : Signatures pour détecter les téléchargements suspects, particulièrement les fichiers packés avec UPX

### Étape 3 : Détection de l'installation d'une porte dérobée
- **HIDS (OSSEC)** : Surveillance de l'intégrité des fichiers système et alerte sur les modifications non autorisées
- **NIDS (Suricata)** : Règles pour détecter le trafic de commande et contrôle (C2)

### Étape 5 : Détection de l'exfiltration de données
- **NIDS (Suricata)** : Surveillance des transferts volumineux vers des serveurs externes
- **Proxy HTTP (Squid)** : Contrôle du trafic sortant HTTP/HTTPS

## Mise en place du proxy HTTP Squid

### Configuration de Squid et SquidGuard

Nous avons configuré Squid pour utiliser SquidGuard comme réécriveur d'URL :

```conf
url_rewrite_program /usr/bin/squidGuard -c /etc/squidguard/squidGuard.conf

acl allowed_ips src 100.80.0.0/16

http_access allow localhost
http_access allow allowed_ips

# And finally deny all other access to this proxy
http_access deny all
```

### Configuration de SquidGuard

Nous avons créé une politique qui :
- Autorise un accès total pour le groupe admin
- Restreint l'accès du groupe users aux heures de bureau et bloque example.com
- Redirige vers perdu.com en cas de violation de politique

```conf
dbhome /etc/squidguard/
logdir /var/log/squidguard/

# Time periods definition
time workhours {
    weekly mtwhf 08:00 - 17:00
}

# Source groups definition
src admin {
    ip 100.80.0.1  # target-router
    ip 100.80.0.2  # target-admin
}

src users {
    ip 100.80.0.3  # target-dev
    ip 100.80.0.4  # target-commercial
    within workhours
}

# Destination definition
dest interdit {
    domainlist interdit-domains.txt
}

# ACL definitions
acl {
    admin {
        pass any
    }
    
    users {
        pass !interdit any
        redirect http://perdu.com
    }
    
    default {
        pass none
        redirect http://perdu.com
    }
}
```

### Liste des domaines interdits
```
example.com
```

### Sécurisation du proxy

Pour rendre l'utilisation du proxy obligatoire et non contournable, la meilleure solution est de combiner :

1. **Redirection transparente** : Configurer iptables pour rediriger tout le trafic HTTP/HTTPS vers le proxy
   ```bash
   iptables -t nat -A PREROUTING -i eth1 -p tcp --dport 80 -j REDIRECT --to-port 3128
   iptables -t nat -A PREROUTING -i eth1 -p tcp --dport 443 -j REDIRECT --to-port 3128
   ```

2. **Règles de pare-feu** : Bloquer tout trafic web sortant direct
   ```bash
   iptables -A FORWARD -i eth1 -p tcp --dport 80 -j DROP
   iptables -A FORWARD -i eth1 -p tcp --dport 443 -j DROP
   ```

3. **Segmentation réseau** : Seul le proxy a accès au réseau externe

## Mise en place du NIDS Suricata

### Configuration de Suricata
Nous avons modifié le fichier de configuration pour charger les règles locales :

```yaml
rule-files:
  - suricata.rules
  - local.rules
```

### Règle de détection pour les fichiers packés UPX
Nous avons créé une règle pour détecter les fichiers packés avec UPX, couramment utilisés par les malwares :

```
# Rule to detect files packed with UPX
alert http any any -> $HOME_NET any (msg:"UPX Packed File Download Detected"; content:"Info: This file is packed with the UPX executable packer http://upx.sf.net"; sid:1000001; rev:1;)
```

Cette règle surveille tout le trafic HTTP et déclenche une alerte lorsqu'un fichier contenant la signature UPX est téléchargé.

## Mise en place du HIDS OSSEC

### Configuration de la surveillance des fichiers
Nous avons configuré OSSEC pour surveiller spécifiquement le répertoire des médias de Dokuwiki :

```xml
<syscheck>
  <frequency>43200</frequency>
  <!-- Remove default directories -->
  <!-- <directories check_all="yes">/etc,/usr/bin,/usr/sbin</directories> -->
  
  <!-- Add Dokuwiki media directory with report_changes to detect new files -->
  <directories check_all="yes" report_changes="yes">/var/lib/dokuwiki/data/media</directories>
</syscheck>
```

### Règle de détection pour les nouveaux fichiers
Nous avons créé une règle personnalisée pour déclencher une alerte lorsque de nouveaux fichiers sont ajoutés dans le répertoire des médias :

```xml
<group name="local,syscheck">
  <rule id="100100" level="7">
    <if_sid>550</if_sid>
    <match>/var/lib/dokuwiki/data/media</match>
    <description>New file detected in Dokuwiki media directory</description>
  </rule>
</group>
```

## Conclusion

Notre solution de détection d'intrusion multicouche permet de :
1. Contrôler le trafic web avec un proxy filtrant
2. Détecter les attaques réseau avec Suricata (NIDS)
3. Surveiller l'intégrité des systèmes avec OSSEC (HIDS)

Cette approche défensive en profondeur offre une protection efficace contre les différentes étapes d'une attaque par ransomware, notamment le téléchargement de fichiers malveillants, l'installation de portes dérobées et l'exfiltration de données. 