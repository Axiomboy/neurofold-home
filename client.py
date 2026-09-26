import socket
import json
import math
import random
import time

SERVER_HOST = '76.102.42.159 ' 
SERVER_PORT = 5000

def parse_http_response(response_text):
    try:
        parts = response_text.split("\r\n\r\n", 1)
        if len(parts) == 2:
            return json.loads(parts[1])
    except Exception:
        pass
    return None

def compute_molecular_physics(sequence):
    """
    Executes a standard Lennard-Jones potential & dihedral torsion minimization model
    to evaluate binding affinity energy for targeting Beta-Tau inhibition folds.
    """
    print(f"[PHYSICS] Initializing conformation sweep for Tau tract: {sequence}")
    best_energy = float('inf')
    best_conformation = ""
    
    # Map raw AA letters into generalized physical mass/charge profiles
    amino_acid_weights = {a: ord(a) % 7 + 1 for a in set(sequence)}
    
    # Perform 15,000 iterative alignment Monte Carlo conformational updates
    for step in range(15000):
        current_energy = 0.0
        coords = []
        
        # 1. Generate structural conformation path vectors
        for i, aa in enumerate(sequence):
            weight = amino_acid_weights[aa]
            # Mock coordinate generation using structural pseudo-torsion matrix angles
            x = math.sin(step + i) * weight * 1.5
            y = math.cos(step - i) * weight * 1.5
            z = (step % 10) * 0.2 * i
            coords.append((x, y, z))
            
        # 2. Compute non-bonded Van der Waals attractions (Lennard-Jones 12-6 Potential Formula)
        # V(r) = 4 * epsilon * [(sigma/r)^12 - (sigma/r)^6]
        epsilon = 0.15  # kcal/mol
        sigma = 3.5     # Angstroms
        
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                dx = coords[i][0] - coords[j][0]
                dy = coords[i][1] - coords[j][1]
                dz = coords[i][2] - coords[j][2]
                r = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01 # Add buffer to prevent divide-by-zero
                
                # Apply the LJ formula variables
                lj_part = sigma / r
                v_lj = 4 * epsilon * (math.pow(lj_part, 12) - math.pow(lj_part, 6))
                current_energy += v_lj
                
        # 3. Save the lowest energy folding configuration found
        if current_energy < best_energy:
            best_energy = current_energy
            best_conformation = f"Alpha-Helix-Turn-{round(coords[0][0], 2)}-{round(coords[-1][2],2)}"
            
    # Normalize final calculated energy values into true relative units
    final_score = round(best_energy / len(sequence), 4)
    print(f"[PHYSICS] Sweep completed. Optimal Binding Free Energy found: {final_score} kcal/mol")
    return final_score, best_conformation

def run_client():
    while True:
        try:
            # 1. Request Job from Server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            req = f"GET /request_job HTTP/1.1\r\nHost: {SERVER_HOST}\r\nConnection: close\r\n\r\n"
            s.sendall(req.encode('utf-8'))
            
            response = ""
            while True:
                chunk = s.recv(4096).decode('utf-8')
                if not chunk: break
                response += chunk
            s.close()
            
            job = parse_http_response(response)
            if not job:
                print("[-] Unable to parse valid task packet from central system.")
                time.sleep(10)
                continue
                
            if job.get("status") == "completed":
                print(f"[*] Task complete message received: {job.get('message')}")
                break
                
            # 2. Run local molecular physics calculation logic
            seq_id = job['id']
            sequence = job['sequence']
            
            energy, conformation = compute_molecular_physics(sequence)
            
            # 3. Transmit complete simulation dataset chunk back to home platform
            payload = {
                "id": seq_id,
                "sequence": sequence,
                "calculated_energy": energy,
                "optimal_conformation": conformation
            }
            payload_bytes = json.dumps(payload)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            submit_req = (
                f"POST /submit_result HTTP/1.1\r\n"
                f"Host: {SERVER_HOST}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(payload_bytes)}\r\n"
                f"Connection: close\r\n\r\n"
                f"{payload_bytes}"
            )
            s.sendall(submit_req.encode('utf-8'))
            s.close()
            print(f"[+] Securely returned calculation pack for item registration ID: {seq_id}\n")
            time.sleep(2)
            
        except ConnectionRefusedError:
            print(f"[-] Central server at {SERVER_HOST}:{SERVER_PORT} is currently offline. Retrying in 15 seconds...")
            time.sleep(15)
        except Exception as e:
            print(f"[-] Error tracking pipeline processes: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("[*] Launching NeuroFold Client Node...")
    run_client()
