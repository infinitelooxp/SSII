import csv
import hashlib
import time
import os
import logging
import configparser
import os.path
from getpass import getpass
from tkinter import messagebox

'''
param: ruta a archivo cvs con las columnas ruta,hash
return: lista de tuplas (ruta,hash)
'''
def read_database(path):
    hashes = []
    with open(path,'r') as csv_file:
        hashes = [(ruta,hash) for ruta,hash in csv.reader(csv_file)]
    return hashes

def get_config_file():
    defaults_paths = ["/etc/hids/config.ini","./config.ini","./hids.ini","./hids.conf"]
    
    for path in defaults_paths:
        if os.path.isfile(path):
            return path
        
    return None
            

def main():
    intervalo = 3600
    log_path = "hids.log"
    db_path = "hids.csv"

    config = configparser.ConfigParser()
    if get_config_file == None:
        print("No se encontró ningún archivo de configuracion")
        
    config.read("hids.ini")
    
    try:
        intervalo = int(config.get("General","intervalo"))
    except Exception as e:
        print(e)
        
    try:
        log_path = config.get("General","log")
    except Exception as e:
        print(e)
        
    try:    
        db_path = config.get("General","database")
    except Exception as e:
        print(e)    
    
    #inicializar log
    log_format = "[%(levelname)s] %(asctime)s : %(message)s"
    logging.basicConfig(level=logging.DEBUG,filename=log_path,format = log_format)
    
    hashes = read_database(db_path)
   
    contra_raw = ""
    try:
        with open(".shadow","r") as pass_fd:
            contra_hash = pass_fd.read()
            
        print("Introduzca la contraseña de administrador:")
    
        contra_raw = getpass()
        pass_hash = hashlib.sha1(contra_raw.encode()).hexdigest()
        
        if contra_hash != pass_hash:
            print("Contraseña erronea")
            exit(-1)
            
    except:
        print("No existe una contraseña almacena o no se puede acceder a ella")
        contra_raw = getpass("Por favor inserte una contraseña:")
        contra_hash = hashlib.sha1(contra_raw.encode()).hexdigest()
        
        try:
            with open(".shadow","x") as pass_fd:
                pass_fd.write(contra_hash)
        except Exception as e:
            print(e)
            print("Fallo al crear la contraseña")
            exit(-1)
        
    logging.info("Arrancando monitor")

    #Bucle principal, ejecutar cada x tiempo
    while True:
        print("Comprobando Integridad")
        
        for ruta,hash in hashes:
            try:
                file_hash = hashlib.sha1(open(ruta).read().encode()).hexdigest()
            except FileNotFoundError as e:
                msg = "===# FICHERO BORRADO! #===\n" \
                        "Ruta: " + ruta
                print(msg)
                logging.error("Fallo en:(" + ruta + ") El fichero no se encuntra")
                
                continue
	
            new_hash = hashlib.sha1((file_hash + contra_raw).encode()).hexdigest()
            if new_hash != hash:
                msg = "===# FICHERO CORRUPTO! #===\n" + \
                        "Ruta: " + ruta + "\n" \
                        "SHA1 Original:\t" + hash + "\n" \
                        "SHA1 Actual:\t" + new_hash 
                print(msg)
                #_ = messagebox.showerror("ARCHIVO CORRUPTO!", msg)
                logging.error("Fallo en:(" + ruta + ") Hash original:(" + hash + ") Actual:(" + new_hash + ")")
            
            logging.info("Integridad comprobada")
             
        print(" -- ")
        
        time.sleep(intervalo)
        
main()