# Script PowerShell pour le nettoyage automatique des fichiers temporaires
# Supprime les fichiers dans temp/ plus anciens que 5 heures

param(
    [string]$TempPath = "temp",
    [int]$MaxAgeHours = 5
)

# Fonction de logging
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
    Add-Content -Path "cleanup.log" -Value "[$timestamp] $Message"
}

Write-Log "=== Début du nettoyage automatique des fichiers temporaires ==="

# Vérifier si le dossier temp existe
if (-not (Test-Path $TempPath)) {
    Write-Log "Le dossier $TempPath n'existe pas"
    exit
}

# Calculer la date limite (5 heures dans le passé)
$cutoffTime = (Get-Date).AddHours(-$MaxAgeHours)
Write-Log "Suppression des fichiers plus anciens que $cutoffTime"

# Obtenir les fichiers plus anciens que 5 heures
$oldFiles = Get-ChildItem -Path $TempPath -File | Where-Object { $_.LastWriteTime -lt $cutoffTime }

$deletedCount = 0
$totalSizeDeleted = 0

foreach ($file in $oldFiles) {
    try {
        $fileSize = $file.Length
        $ageHours = [math]::Round(((Get-Date) - $file.LastWriteTime).TotalHours, 1)
        
        Remove-Item $file.FullName -Force
        $deletedCount++
        $totalSizeDeleted += $fileSize
        
        Write-Log "Supprimé: $($file.Name) (âge: ${ageHours}h, taille: $fileSize bytes)"
    }
    catch {
        Write-Log "Erreur lors de la suppression de $($file.Name): $($_.Exception.Message)"
    }
}

# Résumé
if ($deletedCount -gt 0) {
    $sizeMB = [math]::Round($totalSizeDeleted / 1MB, 2)
    Write-Log "Nettoyage terminé: $deletedCount fichiers supprimés, ${sizeMB} MB libérés"
} else {
    Write-Log "Aucun fichier à supprimer"
}

Write-Log "=== Fin du nettoyage ==="
