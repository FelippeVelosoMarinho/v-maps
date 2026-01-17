from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AvatarBase(BaseModel):
    # Cabelo
    hair_style: str = Field(
        default="waves",
        description="Estilo de cabelo: afro, locks, braids, moicano, waves, careca, curly_long"
    )
    hair_color: str = Field(default="#2C1810", pattern="^#[0-9A-Fa-f]{6}$")
    
    # Físico
    body_type: str = Field(
        default="normal",
        description="Tipo físico: gordinho, magro, forte, normal"
    )
    
    # Rosto
    face_shape: str = Field(
        default="oval",
        description="Formato do rosto: quadrado, retangular, redondo, oval"
    )
    
    # Olhos
    eye_type: str = Field(
        default="normal",
        description="Tipo de olhos: asiatico, fechado, piscando, normal, arregalado"
    )
    eye_color: str = Field(default="#4A3C31", pattern="^#[0-9A-Fa-f]{6}$")
    
    # Pele
    skin_tone: str = Field(default="#F5D5B8", pattern="^#[0-9A-Fa-f]{6}$")
    
    # Roupa
    clothing_style: str = Field(
        default="casual",
        description="Estilo de roupa: casual, formal, esportivo, estampado"
    )
    clothing_color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")
    
    # Acessórios
    has_glasses: bool = False
    has_beard: bool = False
    beard_color: str = Field(default="#2C1810", pattern="^#[0-9A-Fa-f]{6}$")


class AvatarCreate(AvatarBase):
    pass


class AvatarUpdate(BaseModel):
    hair_style: Optional[str] = None
    hair_color: Optional[str] = None
    body_type: Optional[str] = None
    face_shape: Optional[str] = None
    eye_type: Optional[str] = None
    eye_color: Optional[str] = None
    skin_tone: Optional[str] = None
    clothing_style: Optional[str] = None
    clothing_color: Optional[str] = None
    has_glasses: Optional[bool] = None
    has_beard: Optional[bool] = None
    beard_color: Optional[str] = None


class AvatarResponse(AvatarBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Configurações de opções disponíveis
AVATAR_OPTIONS = {
    "hair_styles": [
        {"value": "afro", "label": "Afro"},
        {"value": "locks", "label": "Locks"},
        {"value": "braids", "label": "Tranças"},
        {"value": "moicano", "label": "Moicano"},
        {"value": "waves", "label": "Ondulado"},
        {"value": "careca", "label": "Careca"},
        {"value": "curly_long", "label": "Cacheado Longo"},
    ],
    "body_types": [
        {"value": "magro", "label": "Magro"},
        {"value": "normal", "label": "Normal"},
        {"value": "gordinho", "label": "Gordinho"},
        {"value": "forte", "label": "Forte"},
    ],
    "face_shapes": [
        {"value": "quadrado", "label": "Quadrado"},
        {"value": "retangular", "label": "Retangular"},
        {"value": "redondo", "label": "Redondo"},
        {"value": "oval", "label": "Oval"},
    ],
    "eye_types": [
        {"value": "normal", "label": "Normal"},
        {"value": "asiatico", "label": "Asiático"},
        {"value": "fechado", "label": "Fechado"},
        {"value": "piscando", "label": "Piscando"},
        {"value": "arregalado", "label": "Arregalado"},
    ],
    "clothing_styles": [
        {"value": "casual", "label": "Casual"},
        {"value": "formal", "label": "Formal"},
        {"value": "esportivo", "label": "Esportivo"},
        {"value": "estampado", "label": "Estampado"},
    ],
    "preset_colors": {
        "hair": [
            "#2C1810",  # Preto
            "#4A3C31",  # Castanho escuro
            "#8B7355",  # Castanho claro
            "#E6BE8A",  # Loiro
            "#C93305",  # Ruivo
            "#FFFFFF",  # Branco/Grisalho
            "#FF1493",  # Rosa
            "#9B59B6",  # Roxo
            "#3498DB",  # Azul
            "#2ECC71",  # Verde
        ],
        "skin": [
            "#FFF5E1",  # Pele muito clara
            "#FFE4C4",  # Pele clara
            "#F5D5B8",  # Pele média clara
            "#D4A574",  # Pele média
            "#C68642",  # Pele morena
            "#8D5524",  # Pele escura
            "#5C3317",  # Pele muito escura
        ],
        "clothing": [
            "#3B82F6",  # Azul
            "#EF4444",  # Vermelho
            "#10B981",  # Verde
            "#F59E0B",  # Laranja
            "#8B5CF6",  # Roxo
            "#EC4899",  # Rosa
            "#06B6D4",  # Ciano
            "#84CC16",  # Lima
            "#1F2937",  # Cinza escuro
            "#FFFFFF",  # Branco
        ],
        "eyes": [
            "#4A3C31",  # Castanho escuro
            "#8B7355",  # Castanho claro
            "#3498DB",  # Azul
            "#2ECC71",  # Verde
            "#95A5A6",  # Cinza
            "#1F2937",  # Preto
        ]
    }
}
