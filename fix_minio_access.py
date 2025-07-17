# fix_minio_access.py - Corriger l'accès aux fichiers MinIO

import boto3
import json
from botocore.exceptions import ClientError

def fix_minio_access():
    """Corriger l'accès aux fichiers MinIO"""
    print("Correction de l'accès MinIO...")
    
    try:
        # Client MinIO
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            region_name='us-east-1'
        )
        
        bucket_name = 'django-test'
        
        # 1. Créer le bucket s'il n'existe pas
        try:
            client.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' existe")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f" Création du bucket '{bucket_name}'...")
                client.create_bucket(Bucket=bucket_name)
                print(f" Bucket '{bucket_name}' créé")
        
        # 2. Configurer la politique d'accès public
        print("🔄 Configuration de la politique d'accès...")
        
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
        
        client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(public_policy)
        )
        print("Politique d'accès public configurée")
        
        # 3. Tester l'accès
        print("Test d'accès...")
        
        # Upload un fichier de test
        test_content = "Test d'accès MinIO - OK!"
        test_key = "test/access-test.txt"
        
        client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # URLs d'accès
        direct_url = f"http://localhost:9000/{bucket_name}/{test_key}"
        presigned_url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        
        print(f" Fichier de test créé: {test_key}")
        print(f" URL directe: {direct_url}")
        print(f" URL pré-signée: {presigned_url[:80]}...")
        
        # Lister tous les fichiers
        print("\n Fichiers dans le bucket:")
        response = client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                url = f"http://localhost:9000/{bucket_name}/{obj['Key']}"
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
                print(f"     URL: {url}")
        else:
            print("   Aucun fichier trouvé")
        
        # Nettoyer le fichier de test
        client.delete_object(Bucket=bucket_name, Key=test_key)
        
        print(f"\n MinIO configuré correctement!")
        print(f" Console MinIO: http://localhost:9001")
        print(f" Identifiants: minioadmin / minioadmin123")
        
        return True
        
    except Exception as e:
        print(f" Erreur: {e}")
        return False

if __name__ == "__main__":
    fix_minio_access()