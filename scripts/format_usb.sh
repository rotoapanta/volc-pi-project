#!/bin/bash

# Script para formatear de forma segura una memoria USB montada en /dev/sda1
# ⚠️ Úsalo con precaución. Esto borrará todos los datos de la unidad.

DEVICE="/dev/sda1"
LABEL="RAINDATA"

echo "⚠️  ESTO BORRARÁ TODOS LOS DATOS EN $DEVICE"
echo "¿Estás seguro de que quieres continuar? (yes/no)"
read confirm

if [ "$confirm" != "yes" ]; then
  echo "❌ Operación cancelada."
  exit 1
fi

# Desmontar dispositivo si está montado
if mount | grep $DEVICE > /dev/null; then
  echo "📤 Desmontando $DEVICE..."
  sudo umount $DEVICE
fi

# Formatear a ext4
echo "💾 Formateando $DEVICE como ext4 con etiqueta '$LABEL'..."
sudo mkfs.ext4 -F -L $LABEL $DEVICE

if [ $? -eq 0 ]; then
  echo "✅ Formateo completado. Puedes volver a insertar o montar la unidad."
else
  echo "❌ Error durante el formateo."
fi
