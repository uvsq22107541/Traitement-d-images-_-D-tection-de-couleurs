###########################################################################
import numpy as np
import cv2
import random 
import time
from threading import Thread
from enum import Enum
import math
###########################################################################

#Debut de capturation de video et l'affecter a la variable cap
cap=cv2.VideoCapture(0)

#mettre une image blanche comme fond d'écran (back_ground)
game = cv2.imread("white_bg.jpg")

#le transformer en array (matrice)
background = np.array(game)

#lecture de l'image de la souris
rat = cv2.imread("rat.png")

#lecture de l'image du chat
cat = cv2.imread("chat.png")

#lecture de l'image de la fin de la partie CONGRATULATIONS (une fois que la souris a mangé tous les fromages) ==> gagné
youWon = cv2.imread("you-won.png")

#lecture de l'image de la fin de la partie GAME OVER (une fois que la souris rencontre le chat) ==> perdre
loose = False
youLoose = cv2.imread("you-loose.png")

#initialisation de la position de la souris (position initiale)
actualRatPos = (0,0)

#initialisation de la position du chat (position initiale)
actualCatPos = (0,0)

#Enumération des différentes directions que peu prendre la souris 
#RAT_DIRECTION ,  0:LEFT  , 1 : UP , 2: RIGHT , 3:DOWN , -1 : NO_DIRECTION
class RatDirection(Enum):
    LEFT = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    NO_DIRECTION = -1
    
    
# Récupération des données de l'inteface
listparameters=[]
file=open("inputs.txt","r")
lines=file.readlines()
for line in lines :
    listparameters=line.split(",")
file.close()
print(listparameters)

#Initialisation de la direction de la souris
RAT_DIRECTION = RatDirection.NO_DIRECTION

#Recuperer la taille et la largeur du back_ground
BACKGROUND_WIDTH = len(game[0])
BACKGROUND_HEIGHT = len(game)

##Initialiser les dimensions de la souris (a partir de l'interface)
RAT_WIDTH = int(listparameters[4])
RAT_HEIGHT = int(listparameters[3])

##Initialiser les dimensions du chat
CAT_WIDTH = 60
CAT_HEIGHT = 60

##Initialiser les dimensions du fromage (a partir de l'interface)
CHEESE_WIDTH = int(listparameters[8])
CHEESE_HEIGHT = int(listparameters[7])

##Initialiser les dimensions de l'obstacle (a partir de l'interface)
OBSTACLE_WIDTH = int(listparameters[2])
OBSTACLE_HEIGHT = int(listparameters[1])

#Initialiser le nombre de fromage (a partir de l'interface)
CHEESE_NUM = int(listparameters[6])

#tableau pour sauvegarder les positions des fromages
cheesePositions=[]

#tableau pour sauvegarder les images des fromages
cheeses=[]

#initialiser les nombre d'obstacles  (a partir de l'interface)
OBSTACLE_NUM = int(listparameters[0])

#tableau pour sauvegarder les positions des obstacles
obstaclePositions=[]

#tableau pour sauvegarder les images des obstacles
obstacles=[]

#redimensionner la taille de la souris (car l'image est grande)
defaultRat  = cv2.resize(rat , (RAT_WIDTH,RAT_HEIGHT) )

#redimensionner la taille du chat (car l'image est grande)
defaultCat  = cv2.resize(cat , (CAT_WIDTH,CAT_HEIGHT) )

#Redimensionner la taille de l'image de gain (taille = a la taille du bach ground) une fois gagné
youWon = cv2.resize(youWon,(BACKGROUND_WIDTH,BACKGROUND_HEIGHT))

#Redimensionner la taille de l'image de perte (taille = a la taille du bach ground) une fois perdu
youLoose = cv2.resize(youLoose,(BACKGROUND_WIDTH,BACKGROUND_HEIGHT))

#redimensionner la taille de la souris (car l'image est grande)
actualRat =cv2.resize(rat , (RAT_WIDTH,RAT_HEIGHT) )

#Lecture des frames
ret, frame = cap.read()                  #(Thread 1 : lire la video et l'afficher les frames)

#faire une copie sur les frames car on va faire un traitement d'image en temps réel 
#La copie permet a l'image de ne pas bugguer 
frameCopy = np.array(frame)              #(Thread 2 : traitement des frames)


#############################  Fonction 1 ########################################################
#Lit l'image du fromage et elle l'ajoute au tableau des fromages, puis elle génère une position 
#aléatoire pour chaque fromage, en prenaut en considération que la génération des positions des   
#fromages ne seront pas égaux ou très proches (collées) des positions des obstacles, en comparant 
#la distance entre chaque fromage et les obstacles du jeu  
#################################################################################################
def generateCheesses():
    for i in range(0,CHEESE_NUM):
        cheese = cv2.imread("cheese.png")
        cheese = cv2.resize(cheese, (CHEESE_WIDTH, CHEESE_HEIGHT))
        cheeses.append(cheese)
        randXPos = random.randint(0, BACKGROUND_WIDTH - CHEESE_WIDTH - 1)
        randYPos = random.randint(0, BACKGROUND_HEIGHT - CHEESE_HEIGHT - 1)
        j=0
        # La Contrainte pour que le fromage ne soit pas collé ou chevauché à un obstacle
        while j < OBSTACLE_NUM:
            if abs(obstaclePositions[j][0] - randXPos ) < 31 or abs(obstaclePositions[j][1] - randYPos ) < 31  :
                randXPos = random.randint(0, BACKGROUND_WIDTH - CHEESE_WIDTH - 1)
                randYPos = random.randint(0, BACKGROUND_HEIGHT - CHEESE_HEIGHT - 1)
                j=0
            j+=1

        cheesePositions.append( (randXPos,randYPos) )


#############################  Fonction 2 #######################################################
#Lit l'image de l'obstacle et elle l'ajoute au tableau des obstacless, puis elle génère une 
#position aléatoire pour chaque obstacle  
#################################################################################################
def generateObstacles():
    for i in range(0,OBSTACLE_NUM):
        obstacle = cv2.imread("obstacle.png")
        obstacle = cv2.resize(obstacle, (OBSTACLE_WIDTH,OBSTACLE_HEIGHT))
        obstacles.append(obstacle)
        randXPos = random.randint(0, BACKGROUND_WIDTH - OBSTACLE_WIDTH - 1)
        randYPos = random.randint(0, BACKGROUND_HEIGHT - OBSTACLE_HEIGHT - 1)
        obstaclePositions.append( (randXPos,randYPos) )

#############################  Fonction 3 ##################################################################
#Fonction qui prend en entrée la direction de la souris, et elle la positionne lselon cette direction
#1 si la direction est a GAUCHE ou AUCUNE_DIRECTION laisse l'icone de la souris telle qu'elle est
#la tete de la souris a gauche et sa queue a droite
#2 si la direction est a DROITE inverser l'icone de la souris de telle sorte que la 
#tete de la souris sera à droite et sa queue sera à gauche (image miroire)
#3 si la direction est en BAS Rotation de l'icone 90 degrés dans le sens contraire des aiguilles 
#de la montre  de telle sorte que la tete de la souris sera en bas et sa queue sera en haut
#4 si la direction est en HAUT Rotation de l'icone 90 degrés dans le meme sens des aiguilles 
#de la montre  de telle sorte que la tete de la souris sera en haut et sa queue sera en bas.
#################################################################################################
def changeDirection(direction):
    global RAT_HEIGHT,RAT_WIDTH,RAT_DIRECTION,actualRat,defaultRat

    #si GAUCHE ou PAS_DIRECTION : Laisser l'icone de la souris telle qu'elle est.
    if direction == RatDirection.LEFT :
        RAT_DIRECTION = RatDirection.LEFT
        RAT_WIDTH = len(actualRat[0])
        RAT_HEIGHT = len(actualRat)
        actualRat = defaultRat
        return actualRat
    elif direction == RatDirection.NO_DIRECTION:
        RAT_DIRECTION =RatDirection.NO_DIRECTION
        actualRat=defaultRat
        return actualRat
    #si HAUT : Rotation de l'icone 90 degrés dans le meme sens des aiguilles de la montre .
    elif direction ==RatDirection.UP:
        RAT_DIRECTION =RatDirection.UP
        newRat = cv2.rotate(defaultRat, cv2.ROTATE_90_CLOCKWISE)
        RAT_WIDTH = len(newRat[0])
        RAT_HEIGHT = len(newRat)
        return newRat
    #si DROITE : inverser l'icone de la souris (image miroire)
    elif direction ==RatDirection.RIGHT:
        RAT_DIRECTION =RatDirection.RIGHT
        newRat = cv2.flip(defaultRat,1)
        RAT_WIDTH = len(newRat[0])
        RAT_HEIGHT = len(newRat)
        return newRat
    #si BAS : Rotation de l'icone 90 degrés dans le sens contraire des aiguilles de la montre
    elif direction == RatDirection.DOWN:
        RAT_DIRECTION =RatDirection.DOWN
        newRat = cv2.rotate(defaultRat, cv2.ROTATE_90_COUNTERCLOCKWISE)
        RAT_WIDTH = len(newRat[0])
        RAT_HEIGHT = len(newRat)
        return newRat
    else:
        raise Exception('INVALID RAT_DIRECTION ')

#############################  Fonction 4 ########################################################
# cette fonction assigne tous les objets (souris, fromages, obstacles) qui sont des sous-matrices
#au back_ground qui est la grande matrice (matrice principal) selons leurs positions et dimensions
#################################################################################################
def assignObjectsToBackground():
    global game, RAT_HEIGHT, RAT_WIDTH, actualRat
    
    #copier le back_ground (pixels blancs) dans une variable globale apelée game
    game = np.copy(background)
    
    #Si tous les fromages ont été mangés,afficher l'image de CONGRATULATIONS et sortir
    if CHEESE_NUM == 0:
        game = youWon
        return
    
    #Si perdu (rencontre du chat),afficher l'image de GAME OVER et sortir
    if loose:
        game = youLoose
        return
    
    #Poser tous les objets du jeux (souris, fromages, obstacles, chat) selon leurs positions dans 
    #la variables game
    try:
        game[ actualRatPos[1]: actualRatPos[1] + RAT_HEIGHT , actualRatPos[0]: actualRatPos[0] + RAT_WIDTH ] = actualRat
    except NameError:
        print(NameError)

    try:
        game[ actualCatPos[1]: actualCatPos[1] + CAT_HEIGHT , actualCatPos[0]: actualCatPos[0] + CAT_WIDTH ] = defaultCat
    except NameError:
        print(NameError)

    for i in range(0,OBSTACLE_NUM):
        try:
            game[  obstaclePositions[i][1] : obstaclePositions[i][1] + OBSTACLE_HEIGHT , obstaclePositions[i][0]: obstaclePositions[i][0] + OBSTACLE_WIDTH ] = obstacles[i]
        except NameError:
            print(NameError)

    for i in range(0,CHEESE_NUM):
        try:
            game[  cheesePositions[i][1] : cheesePositions[i][1] + CHEESE_HEIGHT , cheesePositions[i][0]: cheesePositions[i][0] + CHEESE_WIDTH ] = cheeses[i]
        except NameError:
            print(NameError)
####################################################################################################
            
#Appeler les 2 fonctions dans l'ordre pour génerer les obstacles et fromages
generateObstacles()
generateCheesses()

#générer la position initiale de la souris aléatoirement
i=0
randXPos = random.randint(0, BACKGROUND_WIDTH - RAT_WIDTH - 1)
randYPos = random.randint(0, BACKGROUND_HEIGHT - RAT_HEIGHT - 1)

#on prend en considération que la génération de la position initiale de la ouris  
#ne soit pas égale ou très proche (collée) des positions des obstacles,
while i < OBSTACLE_NUM :
    if(abs( randXPos - obstaclePositions[i][0]) < OBSTACLE_WIDTH or abs(randYPos - obstaclePositions[i][1]) < OBSTACLE_HEIGHT ):
        randXPos = random.randint(0, BACKGROUND_WIDTH - RAT_WIDTH - 1)
        randYPos = random.randint(0, BACKGROUND_HEIGHT - RAT_HEIGHT - 1)
        i=0
    i+=1

#initilaiser la souris qu'au debut elle n'a aucune direction
actualRat = changeDirection(RatDirection.NO_DIRECTION)

#assignation de la position a la souris
actualRatPos = (randXPos,randYPos)

#générer la position initiale du chat aléatoirement
randXPos = random.randint(0, BACKGROUND_WIDTH - CAT_WIDTH - 1)
randYPos = random.randint(0, BACKGROUND_HEIGHT - CAT_HEIGHT - 1)

#on prend en considération que la génération de la position initiale du chat 
#ne soit pas égale ou très proche (collée) des positions des obstacles,
while i < OBSTACLE_NUM :
    if(abs( randXPos - obstaclePositions[i][0]) < OBSTACLE_WIDTH or abs(randYPos - obstaclePositions[i][1]) < OBSTACLE_HEIGHT ) \
            or abs( randXPos - actualRatPos[0]) < CAT_WIDTH or abs( randYPos - actualRatPos[1]) < CAT_WIDTH :
        randXPos = random.randint(0, BACKGROUND_WIDTH - RAT_WIDTH - 1)
        randYPos = random.randint(0, BACKGROUND_HEIGHT - RAT_HEIGHT - 1)
        i=0
    i+=1

#assignation de la position au chat
actualCatPos = (randXPos,randYPos)

#poser tous les objets généres dans la grande matrice (back_ground)
assignObjectsToBackground()

#pour la communication entre les threads
imageCopiedFlag = False

#initialisation de la vitesse de la souris (le pas) (Récupérer à partir de l'interface)
STEP = int(listparameters[5]) #vitesse entre 3 et 15

#############################  Fonction 5 ##################################################################
#cette fonction reconnait en "Mode_RGB" les 2 couleurs  de la flèche, en effectuant un test sur les 
#pixels(B,G,R) suivant la couleur qu'on veut reconnaitre tq ces pixels doivent etre superieures ou
#inferieure au seuil imposé 
#puis calcule la somme des pixels pour les 2 couleurs, si les 2 sommes sont > à un certain seuil 
#la fleche sera détéctée 
#puis elle calcule la sommes des positions des pixels des deux couleurs pour calculer ensuite la
#moyenne des positions des pixels des deux couleurs afin de savoir la position de l'une des couleurs
#par rapport à l'autre afin de décider de la direction de déplacement de la souris 
#Toujours suivre la direction de la tete 
#Exemple de cas ou le tete de la flèche est BLEUE et le début de la flèche est ROUGE
#################################################################################################
def traitImage():

    global imageCopiedFlag ,actualRat

    height = len(frameCopy)
    width = len(frameCopy[0])

#tant que l'image n'a pas encore été copié dans le main : boucler
    while True:

        if not imageCopiedFlag:
            continue

        listOfRedPixels = []                #liste des pixels rouges
        listOfBluePixels = []               #liste des pixels bleus
        redPixelsPositionsSum = [0, 0]      #initialiser la somme des position des pixels rouges
        bleuPixelsPositionsSum = [0, 0]     #initialiser le somme des position des pixels bleus

        #frameCopy[y, x, 0] --> Bleu |#frameCopy[y, x, 1] --> Vert| #frameCopy[y, x, 2] --> Rouge
        for y in range(0, height):
            for x in range(0, width):
                #detection de la couleur rouge : R>120, B<100, G<100
                if frameCopy[y, x, 2] > 120 and frameCopy[y, x, 0] < 100 and frameCopy[y, x, 1] < 100:
                    #Si oui,sommer les positions des pixels rouges pour calculer ensuite la moyenne de ces positions
                    redPixelsPositionsSum[0]+=x
                    redPixelsPositionsSum[1] += y
                    listOfRedPixels.append(frameCopy[y,x])
                    
                #detection de la couleur bleue : R<100, B>120, G<100
                if frameCopy[y, x, 0] > 120 and frameCopy[y, x, 1] < 100 and frameCopy[y, x, 2] < 100:
                    #Si oui,sommer les positions des pixels bleus pour calculer ensuite la moyenne de ces positions
                    bleuPixelsPositionsSum[0] += x
                    bleuPixelsPositionsSum[1] += y
                    listOfBluePixels.append(frameCopy[y, x])

        #si on trouve au moins 20 pixels rouges et 20 pixels bleus donc on a un fleche --> calcul moy
        if len(listOfBluePixels) > 20 and len(listOfRedPixels) > 20 :
            redMoy = [0, 0]   #initialiser la moyenne des position des pixels rouges
            #calculer la moy en divisant le somme des positions des pixels rouges sur le nombre des pixels rouges
            redMoy[0] = redPixelsPositionsSum[0] / len(listOfRedPixels)
            redMoy[1] = redPixelsPositionsSum[1] / len(listOfRedPixels)

            bleuMoy = [0, 0]  #initialiser la moyenne des position des pixels bleus
            #calculer la moy en divisant le somme des positions des pixels bleus sur le nombre des pixels bleus
            bleuMoy[0] = bleuPixelsPositionsSum[0] / len(listOfBluePixels)
            bleuMoy[1] = bleuPixelsPositionsSum[1] / len(listOfBluePixels)

            #AFFICHAFE
            print("FLECHE DETECTEE !!!")
            print(" ROUGE : " + str(redMoy[0]) + " " + str(redMoy[1]))
            print(" BLEU : " + str(bleuMoy[0]) + " " + str(bleuMoy[1]))

            #Prise de décision de la direction
            
            #calculer la distance horizontale (diff entre les X) entre les moyennes de positions des pixels rouges et bleus  
            xDef = abs(bleuMoy[0] - redMoy[0])   
            #calculer la distance verticale (diff entre les Y) entre les moyennes de positions des pixels rouges et bleus  
            yDef = abs(bleuMoy[1] - redMoy[1])

            #si la distance horizontale > la distance verticale Alors aller soit à gauche soit à droite (les Y sont très proches entre eux) 
            #car les pixels sont a peu près sur la méme ligne 
            if (xDef > yDef): # RIGHT OR LEFT
                #si la moyenne des positions des pixels bleus > la moyenne des positions des pixels rouges (les X)--> ALLER A DROITE
                if(bleuMoy[0] > redMoy[0]):
                    print(" ALLER A DROITE !!")
                    actualRat =changeDirection(RatDirection.RIGHT)
                else:
                    print(" ALLER A GAUCHE !!")
                    actualRat =changeDirection(RatDirection.LEFT)
            #si la distance horizontale < la distance verticale Alors aller soit en haut soit en bas (les X sont très proches entre eux)
            #car les pixels sont a peu près sur la méme colone
            else:   # UP OR DOWN
                #si la moyenne des positions des pixels bleus > la moyenne des positions des pixels rouges (les Y)--> ALLER EN BAS
                if(bleuMoy[1] > redMoy[1]):
                    print(" ALLER EN BAS !!")
                    actualRat =changeDirection(RatDirection.DOWN)
                else: 
                    print(" ALLER EN HAUT !!!")
                    actualRat =changeDirection(RatDirection.UP)
        else:
            print(" FLECHE NON DETECTEE, AUCUNE DIRECTION !! ")
            actualRat =changeDirection(RatDirection.NO_DIRECTION)
                #cv2.imshow('frameCopy3', frameCopy)
        imageCopiedFlag = False

#############################  Fonction 6 #######################################################
#cette fonction vérifie si la souris est collée (chuavauchement des position de la souris et du 
#fromage) si oui, il l'a supprime et décrémente le nombre de fromages
#################################################################################################
def eatCheeses():
    global cheesePositions, actualRatPos, RAT_WIDTH, RAT_HEIGHT, actualRat, CHEESE_NUM, RAT_DIRECTION
    
    #pour chaque position d'un fromage, calculer la distance entre ce dernier et la position de la souris 
    for pos in cheesePositions:
        xDef = pos[0] - actualRatPos[0]
        yDef = pos[1] - actualRatPos[1]

        dist = math.sqrt( xDef * xDef + yDef*yDef)

        if dist < RAT_WIDTH:
            #suppression du fromage et décrémentation de son nombre
            cheesePositions.remove(pos)
            CHEESE_NUM-=1


#############################  Fonction 7 #######################################################
#cette fonction vérifie si la souris est collée (chuavauchement des position de la souris et du 
#chat) si oui, la partie est perdu --> Sortie
#################################################################################################
def checkCat():
    global loose , actualCatPos, actualRatPos, RAT_WIDTH, RAT_HEIGHT, actualRat, CHEESE_NUM, RAT_DIRECTION


    xDef = actualCatPos[0] - actualRatPos[0]
    yDef = actualCatPos[1] - actualRatPos[1]

    dist = math.sqrt( xDef * xDef + yDef*yDef)

    if dist < RAT_WIDTH:
        loose = True

#############################  Fonction 7 ########################################################
#cette fonction déplace la souris dans la direction détectée en tenant en compte que lorque on 
#des croise obstacle ou les extrémités (pérrimetre du jeu) la souris ne se déplace plus (stagnation)
#ainsi de la vitesse de la souris qui est enfaite une variabe (STEP) contenant un nombre de pixel 
#avec lequel la souris se déplace, si step>0 (a droite ou en bas) sinon (a gauche ou en haut)
#################################################################################################
def moveRat():
    
    global actualRatPos, RAT_DIRECTION, STEP, RAT_WIDTH, BACKGROUND_WIDTH, RAT_HEIGHT, BACKGROUND_HEIGHT
    direction = RAT_DIRECTION

    if direction == RatDirection.NO_DIRECTION:
        return
    #---------------------------------------------------------------------------------------------#
    #Sur X si je vais a gauche alors je dois  
    elif direction == RatDirection.LEFT :
        #controle a chaque fois si ya intersection entre la nouvelle position de la souris et celle de l'obstacle 
        for i in range(0,OBSTACLE_NUM):
            # s'ils ont le mm Y (intersection avec obstacle)       et     (calcul nvl pos de la souris sur x) si intersection avec obstacle<0
            if  abs(obstaclePositions[i][1] - actualRatPos[1]) < RAT_HEIGHT and  abs(obstaclePositions[i][0] + OBSTACLE_WIDTH - (actualRatPos[0] - STEP) ) < STEP:
        #Si oui la souris ne pourra pas bouger a gauche
                return 
        #sinon on la calcule le nouvelle pos sur X en tenant compte que cette position ne dépassera pas l'extrimité gauche du jeu
        if actualRatPos[0] - STEP >= 0 :
            actualRatPos = (actualRatPos[0] - STEP, actualRatPos[1] )
     #---------------------------------------------------------------------------------------------#   
     #Sur Y si je vais en haut alors je dois     
    elif direction == RatDirection.UP:
        #controle a chaque fois si ya intersection entre la nouvelle position de la souris et celle de l'obstacle
        for i in range(0,OBSTACLE_NUM):
             # s'ils ont le mm X (intersection avec obstacle)<            et (calcul nvl pos de la souris sur Y) si intersection avec obstacle<0
            if abs(obstaclePositions[i][0] - actualRatPos[0]) < RAT_HEIGHT and abs(obstaclePositions[i][1] + OBSTACLE_HEIGHT - (actualRatPos[1] - STEP) ) < STEP:
        #Si oui la souris ne pourra pas bouger vers le haut
                return 
        #sinon on la calcule la nouvelle pos sur Y en tenant compte que cette position ne dépassera pas l'extrimité haute du jeu 
        if actualRatPos[0] - STEP >= 0 :
            if actualRatPos[1] - STEP >= 0 :
                actualRatPos = (actualRatPos[0], actualRatPos[1] - STEP)
     #---------------------------------------------------------------------------------------------#
   #Sur X si je vais a droite alors je dois 
    elif direction == RatDirection.RIGHT:
        #controle a chaque fois si ya intersection entre la nouvelle position de la souris et celle de l'obstacle
        for i in range(0,OBSTACLE_NUM):
          # s'ils ont le mm Y (intersection avec obstacle)       et     (calcul nvl pos de la souris sur x) si intersection avec obstacle<0
            if abs(obstaclePositions[i][1] - actualRatPos[1]) < RAT_HEIGHT and abs(obstaclePositions[i][0] - (actualRatPos[0]+ RAT_WIDTH + STEP) ) < STEP:
                #Si oui la souris ne pourra pas bouger vers la droite
                return
        #sinon on la calcule la nouvelle pos sur X en tenant compte que cette position ne dépassera pas l'extrimité droite du jeu
        if actualRatPos[0] + STEP + RAT_WIDTH < BACKGROUND_WIDTH:
            actualRatPos = (actualRatPos[0] + STEP, actualRatPos[1])
    #---------------------------------------------------------------------------------------------#
    #Sur Y si je vais en bas alors je dois
    elif direction == RatDirection.DOWN:
        for i in range(0,OBSTACLE_NUM):
            if abs(obstaclePositions[i][0] - actualRatPos[0]) < RAT_HEIGHT and abs(obstaclePositions[i][1]  - (actualRatPos[1] + RAT_HEIGHT + STEP) ) < STEP:
                return

        if actualRatPos[1] + STEP + RAT_HEIGHT < BACKGROUND_HEIGHT:
            actualRatPos = (actualRatPos[0], actualRatPos[1] + STEP)
    #---------------------------------------------------------------------------------------------#
    else:
        raise Exception('INVALID RAT_DIRECTION ')


#########################  MAIN    #########################################################

cpt = 0

#Thread pour le traitement d'image
t = Thread(target=traitImage, args=())
t.start()

#Lire a partir de la caméra
while(True):
    # Capture frame-par-frame
    ret, frame = cap.read()

    moveRat()
    eatCheeses()
    checkCat()
    # Our operations on the frame come here
    #Pour lire la vidéo en niveau de gris
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret,th1 = cv2.threshold(gray,100,255,cv2.THRESH_BINARY)
    frameCopy = np.array(frame)
    imageCopiedFlag = True
    cv2.imshow('frame',th1)
    assignObjectsToBackground()
    cv2.imshow('game',game)

    #clique sur q pour quitter
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# quand tout est fait, realiser la capture
cap.release()
cv2.destroyAllWindows()