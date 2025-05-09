import pyshark

def extract_timeline(pcap_path, output_path="timeline.txt", max_packets=1000):
    try:
        cap = pyshark.FileCapture(pcap_path, use_json=True)
    except Exception as e:
        print(f"Erreur lors de l'ouverture du fichier PCAP : {e}")
        return

    timeline = []
    count = 0

    print(f"[+] Traitement de {max_packets} paquets depuis '{pcap_path}'...")

    for pkt in cap:
        try:
            time = pkt.frame_info.time_relative
            proto = pkt.highest_layer
            info = pkt.frame_info.comment if hasattr(pkt.frame_info, 'comment') else pkt.layer_name
            timeline.append({
                'No': pkt.number,
                'Time': time,
                'Protocol': proto,
                'Info': info
            })
            count += 1
            if count >= max_packets:
                break
        except AttributeError:
            continue

    cap.close()

    with open(output_path, 'w') as f:
        for entry in timeline:
            f.write(f"{entry['Time']} | Packet {entry['No']} | {entry['Protocol']} | {entry['Info']}\n")

    print(f"[✓] Timeline sauvegardée dans '{output_path}' ({count} paquets)")

if __name__ == "__main__":
    extract_timeline("capture.pcap", output_path="timeline.txt", max_packets=1000)
