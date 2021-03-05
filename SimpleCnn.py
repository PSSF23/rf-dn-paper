# general imports
import numpy as np
import sklearn
from sklearn.metrics import accuracy_score
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import torch.nn.functional as F
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import seaborn as sns; sns.set()
import warnings
warnings.filterwarnings("ignore")


plt.rcParams["legend.loc"] = "best"
plt.rcParams['figure.facecolor'] = 'white'
#%matplotlib inline
names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']

# filter python warnings
def run():
    torch.multiprocessing.freeze_support()
    print('loop')

if __name__ == '__main__':
    run()
                
# prepare CIFAR data

# normalize
scale = np.mean(np.arange(0, 256))
normalize = lambda x: (x - scale) / scale

# train data
cifar_trainset = datasets.CIFAR10(root='./data', train=True, download=True, transform=None)
cifar_train_images = normalize(cifar_trainset.data)
cifar_train_labels = np.array(cifar_trainset.targets)

# test data
cifar_testset = datasets.CIFAR10(root='./data', train=False, download=True, transform=None)
cifar_test_images = normalize(cifar_testset.data)
cifar_test_labels = np.array(cifar_testset.targets)


# transform
transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
trainset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
testset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    
# define a simple CNN arhcitecture
class SimpleCNN32Filter(torch.nn.Module):
    
    def __init__(self):
        super(SimpleCNN32Filter, self).__init__()        
        self.conv1 = torch.nn.Conv2d(3, 32, kernel_size=10, stride=2) # try 64 too, if possible
        self.fc1 = torch.nn.Linear(144*32, 10)
        
    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = x.view(-1, 144*32)
        x = self.fc1(x)
        return(x)




class SimpleCNN32Filter2Layers(torch.nn.Module):
    
    def __init__(self):
        super(SimpleCNN32Filter2Layers, self).__init__()        
        self.conv1 = torch.nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = torch.nn.Conv2d(32, 32, kernel_size=3, stride=1, padding=1)
        self.conv3 = torch.nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.conv4 = torch.nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1)
        self.conv5 = torch.nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.fc1 = torch.nn.Linear(8192, 200)
        self.fc2 = torch.nn.Linear(200, 10)
        self.maxpool = nn.MaxPool2d((2, 2))
        self.bn = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        
    def forward(self, x):
        b = x.shape[0]
        x = F.relu(self.bn(self.conv1(x)))
        x = F.relu(self.bn(self.conv2(x)))
        x = self.maxpool(x)
        x = F.relu(self.bn2(self.conv3(x)))
        x = F.relu(self.bn2(self.conv4(x)))
        x = F.relu(self.bn3(self.conv5(x)))
        x = self.maxpool(x)
        x = x.view(b, -1)
        #print(x.shape)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return(x)
    

def run_cnn(cnn_model, cifar_train_labels, cifar_test_labels, fraction_of_train_samples, class1=3, class2=5):
    # set params
    num_epochs = 20
    learning_rate = 0.001

    class1_indices = np.argwhere(cifar_train_labels==class1).flatten()
    class1_indices = class1_indices[:int(len(class1_indices) * fraction_of_train_samples)]
    class2_indices = np.argwhere(cifar_train_labels==class2).flatten()
    class2_indices = class2_indices[:int(len(class2_indices) * fraction_of_train_samples)]
    train_indices = np.concatenate([class1_indices, class2_indices]) 
    
    train_sampler = torch.utils.data.sampler.SubsetRandomSampler(train_indices)
    train_loader = torch.utils.data.DataLoader(trainset, batch_size=32, sampler=train_sampler)

    test_indices = np.concatenate([np.argwhere(cifar_test_labels==class1).flatten(), np.argwhere(cifar_test_labels==class2).flatten()])
    test_sampler = torch.utils.data.sampler.SubsetRandomSampler(test_indices)

    test_loader = torch.utils.data.DataLoader(testset, batch_size=32,
                                             shuffle=False, sampler=test_sampler)

    # define model
    net = SimpleCNN32Filter()
    net2 = SimpleCNN32Filter2Layers()
    dev = torch.device("cuda:0")
    net.to(dev)
    net2.to(dev)
    # loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(net.parameters(), lr=learning_rate)
    optimizer2 = optim.Adam(net2.parameters(), lr=learning_rate)
    print("here")
    for epoch in range(num_epochs):  # loop over the dataset multiple times

        for i, data in enumerate(train_loader, 0):
            # get the inputs
            inputs, labels = data
            inputs = torch.tensor(inputs).to(dev)
            labels = torch.tensor(labels).to(dev)
            # zero the parameter gradients
            optimizer.zero_grad()
            optimizer2.zero_grad()
            # forward + backward + optimize
            outputs = net(inputs)
            outputs2 = net2(inputs)
            
            loss = criterion(outputs, labels)
            loss2 = criterion(outputs2, labels)
            
            loss.backward()
            loss2.backward()
            
            optimizer.step()
            optimizer2.step()
            
        # test the model
        correct = torch.tensor(0).to(dev)
        total = torch.tensor(0).to(dev)
        correct2 = torch.tensor(0).to(dev)
        
        with torch.no_grad():
            for data in test_loader:
                images, labels = data
                labels = torch.tensor(labels).to(dev)
                images = torch.tensor(images).to(dev)
                outputs = net(images)
                outputs2 = net2(images)
                _, predicted = torch.max(outputs.data, 1)
                _, predicted2 = torch.max(outputs2.data, 1)
                total += labels.size(0)
                correct += (predicted == labels.view(-1)).sum().item()
                correct2 += (predicted2 == labels.view(-1)).sum().item()
        accuracy = float(correct) / float(total)
        accuracy2 = float(correct2) / float(total)
        print("epoch: ", epoch, "Simple: ", accuracy, "complicated: ", accuracy2)
    return accuracy, accuracy2

#class1, class2, fraction_of_train_samples = 0, 1, .002
for class1 in range(1):
    for class2 in range(class1 + 1, 2):
        fraction_of_train_samples_space = np.geomspace(1, 1, num=1) 
            
        # accuracy vs num training samples (one layer cnn (32 filters))
        cnn32 = list()
        cnn32_two_layer = list()
        for fraction_of_train_samples in fraction_of_train_samples_space:
            accu_cnn32, accu_cnn32_2 = 0,0
            trials = 1
            for i in range(trials):
                tempcnn32, tempcnn32_2 = run_cnn(SimpleCNN32Filter, cifar_train_labels, cifar_test_labels, fraction_of_train_samples)
                accu_cnn32 += tempcnn32
                accu_cnn32_2 += tempcnn32_2
            cnn32.append(accu_cnn32 / trials)
            cnn32_two_layer.append(accu_cnn32_2 / trials)
            print("Train Fraction:", str(fraction_of_train_samples))
            print("Cnn32 Accuracy:", str(accu_cnn32 / trials), " Cnn 2 layer Accuracy: ", str(accu_cnn32_2 / trials))
                  
           
            
           
        plt.rcParams['figure.figsize'] = 13, 10
        plt.rcParams['font.size'] = 25
        plt.rcParams['legend.fontsize'] = 16.5
        plt.rcParams['legend.handlelength'] = 2.5
        plt.rcParams['figure.titlesize'] = 20
        plt.rcParams['xtick.labelsize'] = 15
        plt.rcParams['ytick.labelsize'] = 15
        
        fig, ax = plt.subplots() # create a new figure with a default 111 subplot
      
        ax.plot(fraction_of_train_samples_space*10000, cnn32, marker='X', markerfacecolor='red', markersize=8, color='orange', linewidth=3, linestyle="--", label="CNN (32 filters)")
        ax.plot(fraction_of_train_samples_space*10000, cnn32_two_layer, marker='X', markerfacecolor='red', markersize=8, color='orange', linewidth=3, label="CNN Two Layer (32 filters)")
        
        ax.set_xlabel('Number of Train Samples', fontsize=18)
        ax.set_xscale('log')
        ax.set_xticks([i*10000 for i in list(np.geomspace(0.01, 1, num=8))])
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        
        ax.set_ylabel('Accuracy', fontsize=18)
        
        ax.set_title(str(class1) + " (" + names[class1] + ") vs " + str(class2) + "(" + names[class2] + ") classification", fontsize=18)
        plt.legend()
        
        plt.savefig("cifar_results/" + str(class1) + "_vs_" + str(class2) + "cnn")
        table2 = pd.read_csv("cifar_results/" + str(class1) + "_vs_" + str(class2) + '.csv')
        rowname = ['cnn32']
        rowname.extend(cnn32)
        table2.loc[2] = rowname
        rowname2 = ['cnn32_2_layer']
        rowname2.extend(cnn32_two_layer)
        table2.loc[2] = rowname2
        
        table2.to_csv("cifar_results/" + str(class1) + "_vs_" + str(class2) + "cnn.csv", index=False)