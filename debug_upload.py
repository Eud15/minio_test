# debug_upload.py - Diagnostic complet pour les uploads MinIO

import boto3
import os
import django
from botocore.exceptions import ClientError

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minio_project.settings')
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage

def check_minio_connection():
    """Vérifier la connexion MinIO directe"""
    print("🔍 1. Test de connexion MinIO directe...")
    print("=" * 60)
    
    try:
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            region_name='us-east-1'
        )
        
        # Lister les buckets
        response = client.list_buckets()
        print(f"✅ Connexion OK - {len(response['Buckets'])} bucket(s)")
        
        for bucket in response['Buckets']:
            print(f"   📁 {bucket['Name']} (créé: {bucket['CreationDate']})")
        
        return client
        
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def check_bucket_status(client):
    """Vérifier le statut du bucket django-test"""
    print("\n🔍 2. Vérification du bucket 'django-test'...")
    print("=" * 60)
    
    bucket_name = 'django-test'
    
    try:
        # Vérifier si le bucket existe
        client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' existe")
        
        # Lister les objets
        try:
            response = client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' in response:
                print(f"📄 {len(response['Contents'])} objet(s) trouvé(s):")
                for obj in response['Contents']:
                    print(f"   - {obj['Key']}")
                    print(f"     Taille: {obj['Size']} bytes")
                    print(f"     Modifié: {obj['LastModified']}")
                    
                    # Tester l'accès direct
                    direct_url = f"http://localhost:9000/{bucket_name}/{obj['Key']}"
                    print(f"     URL directe: {direct_url}")
                    
                    # Générer URL pré-signée
                    try:
                        presigned_url = client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket_name, 'Key': obj['Key']},
                            ExpiresIn=3600
                        )
                        print(f"     URL pré-signée: {presigned_url[:80]}...")
                    except Exception as e:
                        print(f"     ❌ Erreur URL pré-signée: {e}")
                    
                    print()
            else:
                print("📭 Bucket vide")
                
        except ClientError as e:
            print(f"❌ Erreur listage objets: {e}")
            
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"❌ Bucket '{bucket_name}' n'existe pas")
            
            # Créer le bucket
            try:
                print(f"🔄 Création du bucket '{bucket_name}'...")
                client.create_bucket(Bucket=bucket_name)
                print(f"✅ Bucket '{bucket_name}' créé!")
                
                # Configurer les permissions publiques
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }
                
                import json
                client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                print(f"✅ Politique publique configurée pour '{bucket_name}'")
                
            except Exception as create_error:
                print(f"❌ Erreur création bucket: {create_error}")
        else:
            print(f"❌ Erreur bucket: {e}")

def test_django_storage():
    """Tester le storage Django"""
    print("\n🔍 3. Test du storage Django...")
    print("=" * 60)
    
    print(f"Storage backend: {settings.DEFAULT_FILE_STORAGE}")
    print(f"Bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NON DÉFINI')}")
    print(f"Endpoint: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'NON DÉFINI')}")
    
    try:
        # Test d'écriture
        from django.core.files.base import ContentFile
        import uuid
        
        test_content = f"Test upload Django-MinIO - {uuid.uuid4()}"
        test_filename = f"test-django/{uuid.uuid4()}.txt"
        
        print(f"\n🔄 Upload de test: {test_filename}")
        
        # Sauvegarder
        saved_name = default_storage.save(test_filename, ContentFile(test_content.encode()))
        print(f"✅ Fichier sauvé: {saved_name}")
        
        # Vérifier existence
        if default_storage.exists(saved_name):
            print("✅ Fichier confirmé dans le storage")
            
            # Obtenir URL
            file_url = default_storage.url(saved_name)
            print(f"🌐 URL Django: {file_url}")
            
            # Tester lecture
            try:
                with default_storage.open(saved_name, 'r') as f:
                    read_content = f.read()
                    if read_content == test_content:
                        print("✅ Contenu vérifié - lecture/écriture OK")
                    else:
                        print("❌ Contenu différent")
            except Exception as e:
                print(f"⚠️ Erreur lecture: {e}")
            
            # Nettoyer
            default_storage.delete(saved_name)
            print("🗑️ Fichier de test supprimé")
            
            return True
        else:
            print("❌ Fichier non trouvé dans le storage")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test Django storage: {e}")
        return False

def test_access_methods():
    """Tester différentes méthodes d'accès"""
    print("\n🔍 4. Test des méthodes d'accès...")
    print("=" * 60)
    
    client = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin123',
        region_name='us-east-1'
    )
    
    bucket_name = 'django-test'
    test_key = 'test-access/sample.txt'
    test_content = "Test d'accès aux fichiers MinIO"
    
    try:
        # Upload un fichier de test
        print(f"🔄 Upload fichier test: {test_key}")
        client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print("✅ Upload réussi")
        
        # Test 1: Accès direct
        direct_url = f"http://localhost:9000/{bucket_name}/{test_key}"
        print(f"\n📱 URL directe: {direct_url}")
        
        # Test 2: URL pré-signée
        presigned_url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print(f"🔑 URL pré-signée: {presigned_url[:80]}...")
        
        # Test 3: Test avec curl (si disponible)
        print(f"\n🔧 Pour tester l'accès, essayez:")
        print(f"   curl -I \"{direct_url}\"")
        print(f"   curl -I \"{presigned_url}\"")
        
        # Nettoyer
        client.delete_object(Bucket=bucket_name, Key=test_key)
        print("\n🗑️ Fichier de test supprimé")
        
    except Exception as e:
        print(f"❌ Erreur test accès: {e}")

def fix_bucket_policy():
    """Corriger la politique du bucket pour l'accès public"""
    print("\n🔍 5. Configuration de la politique d'accès...")
    print("=" * 60)
    
    try:
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            region_name='us-east-1'
        )
        
        bucket_name = 'django-test'
        
        # Politique pour accès public en lecture
        public_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        import json
        client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(public_policy)
        )
        
        print(f"✅ Politique d'accès public configurée pour '{bucket_name}'")
        print("📋 Les fichiers sont maintenant accessibles directement via URL")
        
    except Exception as e:
        print(f"❌ Erreur configuration politique: {e}")
        print("⚠️ Les fichiers nécessiteront des URLs pré-signées")

def main():
    """Diagnostic complet"""
    print("🚀 DIAGNOSTIC COMPLET UPLOAD MINIO")
    print("=" * 80)
    
    # 1. Test connexion
    client = check_minio_connection()
    if not client:
        print("\n❌ Impossible de continuer - MinIO inaccessible")
        return
    
    # 2. Vérifier bucket
    check_bucket_status(client)
    
    # 3. Test Django storage
    django_ok = test_django_storage()
    
    # 4. Test méthodes d'accès
    test_access_methods()
    
    # 5. Corriger politique
    fix_bucket_policy()
    
    # Résumé
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ ET SOLUTIONS")
    print("=" * 80)
    
    if django_ok:
        print("✅ Django-MinIO configuré correctement")
    else:
        print(" Problème avec la configuration Django-MinIO")
    
    print("\n Pour voir vos fichiers:")
    print("   1. Console MinIO: http://localhost:9001")
    print("   2. Bucket: django-test")
    print("   3. Identifiants: minioadmin / minioadmin123")
    
    print("\n URLs d'accès:")
    print("   - Direct: http://localhost:9000/django-test/chemin/fichier")
    print("   - Console: http://localhost:9001")
    print("   - Django: http://127.0.0.1:8000")

if __name__ == "__main__":
    main()