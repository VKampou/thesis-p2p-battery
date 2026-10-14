# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 14:32:59 2022

@author: vaska
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def plot_MUF(ltb,lts, Number_of_ln_values, ln_values, energy_values):
    lt_b=ltb
    lt_s=lts
    N=Number_of_ln_values
    ln=ln_values
    e=energy_values
    
    ##create data for the dashed lines of lt_b and lt_s
    if e[0]<=e[N-1]:
        x2=np.linspace(e[0], e[N-1], 2)
    else:
        x2=np.linspace(e[N-1], e[0], 2)
    y2=x2-x2+lt_s #lt_s
    y3=x2-x2+lt_b#lt_b
    
    fig, ax = plt.subplots()
    
    ax.plot(e, ln, '-o', ms=20, alpha=0.7, mfc='orange')
    ax.plot(x2, y2, '--k', label='λt_s')
    ax.plot(x2, y3, '--k', label='΄λt_b')
    ax.set_title('MUF')
    ax.set_ylabel('PRICE OF ENERGY')
    ax.set_xlabel('ENERGY WILLING TO TRADE')
    
    ax.grid()
    #fig.figimage(im, 10, 10, zorder=3, alpha=.5)
    
    plt.show()
plot_MUF
    
    
def plot_scenarios(loads,realization,Number_of_Scenarios):
    df=pd.DataFrame()
    df=loads
    df['index']=df.index
    W=Number_of_Scenarios
    t = df['index']
    s=realization

    fig, ax = plt.subplots()
    for w in range(W-1):
        ax.plot(t, df['scenario '+str(w)], 'r')  
    ax.plot(t, df['scenario '+str(W-1)], 'r', label='Generated_scenarios') #επιλεγω να βαλω την τελευτααι επαναλυψη χωριστα για να βαλω εκει το label
    ax.plot(t, s, 'b', label='Realization')
    ax.set(xlabel='Time step', ylabel='Load',
    title='Scenarios')
    ax.grid()
    fig.savefig("test.png")
    plt.legend(loc='upper left')
    plt.show()